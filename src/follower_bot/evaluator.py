import itertools
import operator
import re
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable, List

from pydantic import BaseModel, Field

from .model import GithubUser


class FilterRule(BaseModel):
    filter_keys: List[str] = Field(description="Filter keys")
    pattern: str = Field(description="Filter rule in regular expression format")
    check_func: Callable[[str, Any], bool] = Field(
        description="Check function to filter users"
    )


operator_mapping = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def check_number(rule: str, value: int) -> bool:
    if ".." in rule:
        start, end = rule.split("..", 1)
        return start <= str(value) <= end

    op, num = re.match(r"([><]=?)(\d+)", rule).groups()
    return operator_mapping[op](value, int(num))


def check_string(rule: str, value: str) -> bool:
    rule = rule.replace("+", " ")
    return rule.lower() in value.lower()


def check_date(rule: str, value: datetime) -> bool:
    if ".." in rule:
        start, end = rule.split("..", 1)
        start_date = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        end_date = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
        return start_date <= value <= end_date
    else:
        op, date_str = re.match(r"([><]=?)(\d{4}-\d{2}-\d{2})", rule).groups()
        date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        return operator_mapping[op](value, date)


filter_rules: List[FilterRule] = [
    FilterRule(
        filter_keys=["repos", "gists", "followers", "following"],
        pattern=r"^((\d+\.\.)|(([><]=?)?))\d+$",
        check_func=check_number,
    ),
    FilterRule(
        filter_keys=["login", "name", "company", "location", "email"],
        pattern=r"^.*$",
        check_func=check_string,
    ),
    FilterRule(
        filter_keys=["updated"],
        pattern=r"^((\d{4}-\d{2}-\d{2}\.\.)|(([><]=?)?))\d{4}-\d{2}-\d{2}$",
        check_func=check_date,
    ),
]

supported_keys = list(
    itertools.chain.from_iterable(rule.filter_keys for rule in filter_rules)
)


class TokenType(IntEnum):
    LPAREN = 1
    RPAREN = 2
    AND = 4
    OR = 8
    NOT = 16

    RULE = 32


class Token:
    def __init__(self, type, value, start, end):
        self.type: TokenType = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        s = f"{self.type.name}[{self.start},{self.end}]"
        if self.type == TokenType.RULE:
            s += f"({self.value})"
        return s


def scan(expr: str) -> List[Token]:
    tokens: List[Token] = []
    mapping = {
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "&": TokenType.AND,
        "|": TokenType.OR,
        "!": TokenType.NOT,
    }
    index, length = 0, len(expr)

    def is_operator(c: str) -> bool:
        return c in mapping

    while index < length:
        c = expr[index]
        if is_operator(c):
            tokens.append(Token(mapping[c], "", index, index + 1))
            index += 1
        elif c.isspace():
            index += 1
        else:
            start = index
            while (
                index < length
                and not is_operator(expr[index])
                and not expr[index].isspace()
            ):
                index += 1
            tokens.append(Token(TokenType.RULE, expr[start:index], start, index))

    return tokens


def infix_to_postfix(tokens: List[Token]) -> List[Token]:
    stack: List[Token] = []
    postfix: List[Token] = []

    for token in tokens:
        if token.type == TokenType.RULE:
            postfix.append(token)
        elif token.type == TokenType.NOT:
            stack.append(token)
        elif token.type == TokenType.LPAREN:
            stack.append(token)
        elif token.type == TokenType.RPAREN:
            while stack[-1].type != TokenType.LPAREN:
                postfix.append(stack.pop())
            stack.pop()
        elif token.type in (TokenType.AND, TokenType.OR):
            while stack and stack[-1].type in (TokenType.AND, TokenType.OR):
                postfix.append(stack.pop())
            stack.append(token)

    while stack:
        postfix.append(stack.pop())
    return postfix


def validate(tokens: List[Token]) -> None:
    paren_stack: List[Token] = []
    expected: List[TokenType] = [TokenType.RULE, TokenType.NOT, TokenType.LPAREN]

    for i, token in enumerate(tokens):
        token_type = token.type
        if token_type == TokenType.LPAREN:
            paren_stack.append(token)
            expected = [TokenType.RULE, TokenType.NOT, TokenType.LPAREN]

        elif token_type == TokenType.RPAREN:
            if not paren_stack:
                raise ValueError(f"Mismatched parentheses: {token}")
            paren_stack.pop()
            expected = [TokenType.AND, TokenType.OR, TokenType.RPAREN]

        elif token_type == TokenType.RULE:
            if TokenType.RULE not in expected:
                raise ValueError(f"Unexpected rule: {token}")

            if ":" not in token.value:
                raise ValueError(f"Invalid rule: {token}")

            name, value = token.value.split(":", 1)
            for rule in filter_rules:
                if name in rule.filter_keys:
                    if not re.match(rule.pattern, value):
                        raise ValueError(f"Invalid rule: {token}")
                    break
            else:
                raise ValueError(
                    f"Unsupported rule: {token}, supported rules: {supported_keys}"
                )

            expected = [TokenType.AND, TokenType.OR, TokenType.RPAREN]

        elif token_type == TokenType.NOT:
            if TokenType.NOT not in expected:
                raise ValueError(f"Unexpected operator: {token}")
            expected = [TokenType.RULE, TokenType.LPAREN]

        elif token_type in (TokenType.AND, TokenType.OR):
            if token_type not in expected:
                raise ValueError(f"Unexpected binary operator: {token}")
            expected = [TokenType.RULE, TokenType.NOT, TokenType.LPAREN]

        if i == len(tokens) - 1 and token_type in [
            TokenType.AND,
            TokenType.OR,
            TokenType.NOT,
        ]:
            raise ValueError("Expression ends with operator")

    if paren_stack:
        raise ValueError(f"Mismatched parentheses: {paren_stack[-1]}")


def evaluate(postfix_tokens: List[Token], user: GithubUser) -> bool:
    def rule_token_to_bool(rule_token: Token, user: GithubUser) -> bool:
        key, rule = rule_token.value.split(":", 1)
        for rule_item in filter_rules:
            if key not in rule_item.filter_keys:
                continue
            value = getattr(user, key)
            if value is None:
                # default to True if the value is None
                return False
            return rule_item.check_func(rule, value)
        return False

    stack: List[bool] = []
    for token in postfix_tokens:
        if token.type == TokenType.RULE:
            stack.append(rule_token_to_bool(token, user))
        elif token.type == TokenType.AND:
            b = stack.pop()
            a = stack.pop()
            stack.append(a and b)
        elif token.type == TokenType.OR:
            b = stack.pop()
            a = stack.pop()
            stack.append(a or b)
        elif token.type == TokenType.NOT:
            a = stack.pop()
            stack.append(not a)

    if not stack:
        return True
    return stack.pop()
