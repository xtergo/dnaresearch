from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ReactionType(Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    HELPFUL = "helpful"
    INSIGHTFUL = "insightful"


class CommentStatus(Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"


@dataclass
class Comment:
    comment_id: str
    theory_id: str
    theory_version: str
    author: str
    content: str
    parent_comment_id: Optional[str]
    status: CommentStatus
    created_at: str
    updated_at: Optional[str]
    reactions: Dict[str, int]  # reaction_type -> count
    mentions: List[str]  # mentioned usernames


@dataclass
class Reaction:
    reaction_id: str
    comment_id: str
    user_id: str
    reaction_type: ReactionType
    created_at: str


class CollaborationManager:
    def __init__(self):
        self.comments: Dict[str, Comment] = {}
        self.reactions: Dict[str, Reaction] = {}
        self.comment_counter = 0
        self.reaction_counter = 0

    def add_comment(
        self,
        theory_id: str,
        theory_version: str,
        author: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ) -> Comment:
        """Add a comment to a theory"""
        self.comment_counter += 1
        comment_id = f"comment_{theory_id}_{self.comment_counter:06d}"

        # Extract mentions from content
        mentions = self._extract_mentions(content)

        comment = Comment(
            comment_id=comment_id,
            theory_id=theory_id,
            theory_version=theory_version,
            author=author,
            content=content,
            parent_comment_id=parent_comment_id,
            status=CommentStatus.ACTIVE,
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=None,
            reactions={},
            mentions=mentions,
        )

        self.comments[comment_id] = comment
        return comment

    def get_theory_comments(
        self, theory_id: str, theory_version: str, include_deleted: bool = False
    ) -> List[Comment]:
        """Get all comments for a theory"""
        comments = []
        for comment in self.comments.values():
            if (
                comment.theory_id == theory_id
                and comment.theory_version == theory_version
            ):
                if include_deleted or comment.status == CommentStatus.ACTIVE:
                    comments.append(comment)

        # Sort by creation time
        return sorted(comments, key=lambda c: c.created_at)

    def get_comment_thread(self, parent_comment_id: str) -> List[Comment]:
        """Get all replies to a comment"""
        replies = []
        for comment in self.comments.values():
            if comment.parent_comment_id == parent_comment_id:
                if comment.status == CommentStatus.ACTIVE:
                    replies.append(comment)

        return sorted(replies, key=lambda c: c.created_at)

    def update_comment(self, comment_id: str, content: str, author: str) -> bool:
        """Update a comment's content"""
        if comment_id not in self.comments:
            return False

        comment = self.comments[comment_id]
        if comment.author != author:
            return False

        comment.content = content
        comment.updated_at = datetime.utcnow().isoformat() + "Z"
        comment.mentions = self._extract_mentions(content)
        return True

    def delete_comment(self, comment_id: str, author: str) -> bool:
        """Delete a comment (soft delete)"""
        if comment_id not in self.comments:
            return False

        comment = self.comments[comment_id]
        if comment.author != author:
            return False

        comment.status = CommentStatus.DELETED
        comment.updated_at = datetime.utcnow().isoformat() + "Z"
        return True

    def add_reaction(
        self, comment_id: str, user_id: str, reaction_type: ReactionType
    ) -> bool:
        """Add or update a reaction to a comment"""
        if comment_id not in self.comments:
            return False

        # Remove existing reaction from this user
        self._remove_user_reaction(comment_id, user_id)

        # Add new reaction
        self.reaction_counter += 1
        reaction_id = f"reaction_{comment_id}_{self.reaction_counter:06d}"

        reaction = Reaction(
            reaction_id=reaction_id,
            comment_id=comment_id,
            user_id=user_id,
            reaction_type=reaction_type,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        self.reactions[reaction_id] = reaction

        # Update comment reaction counts
        self._update_comment_reactions(comment_id)
        return True

    def remove_reaction(self, comment_id: str, user_id: str) -> bool:
        """Remove a user's reaction from a comment"""
        removed = self._remove_user_reaction(comment_id, user_id)
        if removed:
            self._update_comment_reactions(comment_id)
        return removed

    def get_comment_reactions(self, comment_id: str) -> Dict[str, int]:
        """Get reaction counts for a comment"""
        if comment_id not in self.comments:
            return {}
        return self.comments[comment_id].reactions.copy()

    def get_user_mentions(self, username: str) -> List[Comment]:
        """Get all comments that mention a user"""
        mentions = []
        for comment in self.comments.values():
            if username in comment.mentions and comment.status == CommentStatus.ACTIVE:
                mentions.append(comment)

        return sorted(mentions, key=lambda c: c.created_at, reverse=True)

    def get_collaboration_stats(self, theory_id: str, theory_version: str) -> Dict:
        """Get collaboration statistics for a theory"""
        comments = self.get_theory_comments(theory_id, theory_version)

        total_comments = len(comments)
        unique_contributors = len(set(c.author for c in comments))
        total_reactions = sum(sum(c.reactions.values()) for c in comments)

        # Count threaded discussions
        threaded_comments = sum(1 for c in comments if c.parent_comment_id is not None)

        return {
            "total_comments": total_comments,
            "unique_contributors": unique_contributors,
            "total_reactions": total_reactions,
            "threaded_comments": threaded_comments,
            "has_active_discussion": total_comments > 0,
        }

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment content"""
        import re

        # Match @username but not email addresses (no @ before the @)
        mentions = re.findall(r"(?<!\w)@([\w.]+)", content)
        return list(set(mentions))  # Remove duplicates

    def _remove_user_reaction(self, comment_id: str, user_id: str) -> bool:
        """Remove existing reaction from user for a comment"""
        removed = False
        to_remove = []

        for reaction_id, reaction in self.reactions.items():
            if reaction.comment_id == comment_id and reaction.user_id == user_id:
                to_remove.append(reaction_id)
                removed = True

        for reaction_id in to_remove:
            del self.reactions[reaction_id]

        return removed

    def _update_comment_reactions(self, comment_id: str):
        """Update reaction counts for a comment"""
        if comment_id not in self.comments:
            return

        # Count reactions by type
        reaction_counts = {}
        for reaction in self.reactions.values():
            if reaction.comment_id == comment_id:
                reaction_type = reaction.reaction_type.value
                reaction_counts[reaction_type] = (
                    reaction_counts.get(reaction_type, 0) + 1
                )

        self.comments[comment_id].reactions = reaction_counts
