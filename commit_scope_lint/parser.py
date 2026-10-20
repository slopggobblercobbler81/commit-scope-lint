"""Conventional Commits 1.0.0 message parser."""

import re
from typing import List, Optional, Tuple
from .models import CommitMessage

HEADER_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z0-9_\-]+)"
    r"(?:\((?P<scope>[^()\r\n]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<subject>.*)$"
)

FOOTER_TOKEN_PATTERN = re.compile(
    r"^(?P<token>BREAKING CHANGE|BREAKING-CHANGE|[A-Za-z0-9_\-]+)(?::\s*|\s+#)(?P<value>.*)$"
)


def clean_git_comments(raw: str) -> str:
    """Strip git comment lines (starting with '#') typically found in COMMIT_EDITMSG."""
    lines = raw.splitlines()
    filtered = [line for line in lines if not line.strip().startswith("#")]
    return "\n".join(filtered).strip()


def parse_commit_message(
    raw: str,
    commit_hash: Optional[str] = None,
    author: Optional[str] = None,
    strip_comments: bool = False,
) -> CommitMessage:
    """Parse a commit message string into a structured CommitMessage object."""
    text = raw.replace("\r\n", "\n")
    if strip_comments:
        text = clean_git_comments(text)
    
    # Preserve original lines but find the header
    raw_lines = text.split("\n")
    if not raw_lines or not raw_lines[0].strip():
        # Empty commit message
        return CommitMessage(
            raw=raw,
            header="",
            commit_hash=commit_hash,
            author=author,
        )

    header = raw_lines[0]
    match = HEADER_PATTERN.match(header.strip())

    msg_type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking = False
    subject: Optional[str] = None

    if match:
        msg_type = match.group("type")
        raw_scope = match.group("scope")
        scope = raw_scope.strip() if raw_scope is not None else None
        is_breaking = bool(match.group("breaking"))
        subject = match.group("subject").strip()

    body_lines: List[str] = []
    footers: List[Tuple[str, str]] = []

    remaining_lines = raw_lines[1:]
    
    # Process body and footers
    if remaining_lines:
        # Separate into paragraphs by blank lines
        paragraphs: List[List[str]] = []
        current_para: List[str] = []

        for line in remaining_lines:
            if not line.strip():
                if current_para:
                    paragraphs.append(current_para)
                    current_para = []
            else:
                current_para.append(line)
        if current_para:
            paragraphs.append(current_para)

        # Identify which paragraphs at the end are footers
        footer_paragraphs: List[List[str]] = []
        body_paragraphs: List[List[str]] = []

        # Check paragraphs from the end upwards
        reached_body = False
        for para in reversed(paragraphs):
            if reached_body:
                body_paragraphs.insert(0, para)
                continue

            first_line = para[0].strip()
            footer_match = FOOTER_TOKEN_PATTERN.match(first_line)
            if footer_match:
                footer_paragraphs.insert(0, para)
            else:
                reached_body = True
                body_paragraphs.insert(0, para)

        # Parse collected footers
        for para in footer_paragraphs:
            current_token: Optional[str] = None
            current_value_lines: List[str] = []

            for line in para:
                line_str = line.strip()
                fmatch = FOOTER_TOKEN_PATTERN.match(line_str)
                if fmatch:
                    if current_token is not None:
                        footers.append((current_token, "\n".join(current_value_lines).strip()))
                    current_token = fmatch.group("token")
                    val = fmatch.group("value").strip()
                    current_value_lines = [val] if val else []
                else:
                    if current_token is not None:
                        current_value_lines.append(line_str)

            if current_token is not None:
                footers.append((current_token, "\n".join(current_value_lines).strip()))

        # Reconstruct body
        body_line_chunks: List[str] = []
        for i, para in enumerate(body_paragraphs):
            body_line_chunks.extend(para)
            if i < len(body_paragraphs) - 1:
                body_line_chunks.append("")
        
        body_lines = body_line_chunks
        body_text = "\n".join(body_line_chunks).strip() if body_line_chunks else None
    else:
        body_text = None

    # Check if any footer is BREAKING CHANGE
    for token, _ in footers:
        if token in ("BREAKING CHANGE", "BREAKING-CHANGE"):
            is_breaking = True

    return CommitMessage(
        raw=raw,
        header=header,
        type=msg_type,
        scope=scope,
        is_breaking=is_breaking,
        subject=subject,
        body=body_text,
        body_lines=body_lines,
        footers=footers,
        commit_hash=commit_hash,
        author=author,
    )
