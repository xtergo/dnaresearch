from collaboration_manager import CollaborationManager, CommentStatus, ReactionType


class TestCollaborationManager:
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = CollaborationManager()

    def test_add_comment(self):
        """Test adding a comment to a theory"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Great theory! This looks promising.",
        )

        assert comment.theory_id == "autism-theory-1"
        assert comment.theory_version == "1.0.0"
        assert comment.author == "dr.researcher"
        assert comment.content == "Great theory! This looks promising."
        assert comment.parent_comment_id is None
        assert comment.status == CommentStatus.ACTIVE
        assert comment.comment_id.startswith("comment_autism-theory-1_")

    def test_add_reply_comment(self):
        """Test adding a reply to an existing comment"""
        # Add parent comment
        parent = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Original comment",
        )

        # Add reply
        reply = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.smith",
            content="I agree with your analysis.",
            parent_comment_id=parent.comment_id,
        )

        assert reply.parent_comment_id == parent.comment_id
        assert reply.author == "dr.smith"

    def test_extract_mentions(self):
        """Test extracting @mentions from comment content"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Have you seen @dr.smith and @dr.jones work on this?",
        )

        assert "dr.smith" in comment.mentions
        assert "dr.jones" in comment.mentions
        assert len(comment.mentions) == 2

    def test_get_theory_comments(self):
        """Test retrieving all comments for a theory"""
        # Add multiple comments
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="First comment",
        )
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.smith",
            content="Second comment",
        )

        comments = self.manager.get_theory_comments("autism-theory-1", "1.0.0")
        assert len(comments) == 2
        assert comments[0].content == "First comment"
        assert comments[1].content == "Second comment"

    def test_get_comment_thread(self):
        """Test retrieving replies to a comment"""
        # Add parent comment
        parent = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Parent comment",
        )

        # Add replies
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.smith",
            content="First reply",
            parent_comment_id=parent.comment_id,
        )
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.jones",
            content="Second reply",
            parent_comment_id=parent.comment_id,
        )

        replies = self.manager.get_comment_thread(parent.comment_id)
        assert len(replies) == 2
        assert all(reply.parent_comment_id == parent.comment_id for reply in replies)

    def test_update_comment(self):
        """Test updating a comment's content"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Original content",
        )

        # Update by same author
        success = self.manager.update_comment(
            comment.comment_id, "Updated content", "dr.researcher"
        )
        assert success
        assert self.manager.comments[comment.comment_id].content == "Updated content"
        assert self.manager.comments[comment.comment_id].updated_at is not None

        # Try to update by different author
        success = self.manager.update_comment(
            comment.comment_id, "Unauthorized update", "dr.smith"
        )
        assert not success

    def test_delete_comment(self):
        """Test soft deleting a comment"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="To be deleted",
        )

        # Delete by same author
        success = self.manager.delete_comment(comment.comment_id, "dr.researcher")
        assert success
        assert self.manager.comments[comment.comment_id].status == CommentStatus.DELETED

        # Try to delete by different author
        comment2 = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.smith",
            content="Another comment",
        )
        success = self.manager.delete_comment(comment2.comment_id, "dr.researcher")
        assert not success

    def test_add_reaction(self):
        """Test adding reactions to comments"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Great insight!",
        )

        # Add like reaction
        success = self.manager.add_reaction(
            comment.comment_id, "user1", ReactionType.LIKE
        )
        assert success
        assert self.manager.comments[comment.comment_id].reactions["like"] == 1

        # Add helpful reaction from different user
        success = self.manager.add_reaction(
            comment.comment_id, "user2", ReactionType.HELPFUL
        )
        assert success
        assert self.manager.comments[comment.comment_id].reactions["helpful"] == 1

        # Change reaction from same user
        success = self.manager.add_reaction(
            comment.comment_id, "user1", ReactionType.INSIGHTFUL
        )
        assert success
        assert self.manager.comments[comment.comment_id].reactions.get("like", 0) == 0
        assert self.manager.comments[comment.comment_id].reactions["insightful"] == 1

    def test_remove_reaction(self):
        """Test removing reactions from comments"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Great insight!",
        )

        # Add reaction
        self.manager.add_reaction(comment.comment_id, "user1", ReactionType.LIKE)
        assert self.manager.comments[comment.comment_id].reactions["like"] == 1

        # Remove reaction
        success = self.manager.remove_reaction(comment.comment_id, "user1")
        assert success
        assert self.manager.comments[comment.comment_id].reactions.get("like", 0) == 0

    def test_get_user_mentions(self):
        """Test retrieving comments that mention a user"""
        # Add comments with mentions
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Great work @dr.smith!",
        )
        self.manager.add_comment(
            theory_id="cancer-theory-1",
            theory_version="1.0.0",
            author="dr.jones",
            content="@dr.smith what do you think about this approach?",
        )
        self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="No mentions here",
        )

        mentions = self.manager.get_user_mentions("dr.smith")
        assert len(mentions) == 2
        assert all("dr.smith" in comment.mentions for comment in mentions)

    def test_collaboration_stats(self):
        """Test getting collaboration statistics for a theory"""
        theory_id = "autism-theory-1"
        theory_version = "1.0.0"

        # Add comments from different authors
        comment1 = self.manager.add_comment(
            theory_id=theory_id,
            theory_version=theory_version,
            author="dr.researcher",
            content="First comment",
        )
        self.manager.add_comment(
            theory_id=theory_id,
            theory_version=theory_version,
            author="dr.smith",
            content="Second comment",
        )
        self.manager.add_comment(
            theory_id=theory_id,
            theory_version=theory_version,
            author="dr.researcher",
            content="Reply to first",
            parent_comment_id=comment1.comment_id,
        )

        # Add reactions
        self.manager.add_reaction(comment1.comment_id, "user1", ReactionType.LIKE)
        self.manager.add_reaction(comment1.comment_id, "user2", ReactionType.HELPFUL)

        stats = self.manager.get_collaboration_stats(theory_id, theory_version)
        assert stats["total_comments"] == 3
        assert stats["unique_contributors"] == 2
        assert stats["total_reactions"] == 2
        assert stats["threaded_comments"] == 1
        assert stats["has_active_discussion"] is True

    def test_empty_theory_stats(self):
        """Test stats for theory with no comments"""
        stats = self.manager.get_collaboration_stats("empty-theory", "1.0.0")
        assert stats["total_comments"] == 0
        assert stats["unique_contributors"] == 0
        assert stats["total_reactions"] == 0
        assert stats["threaded_comments"] == 0
        assert stats["has_active_discussion"] is False

    def test_reaction_types(self):
        """Test all supported reaction types"""
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Test comment",
        )

        # Test all reaction types
        reaction_types = [
            ReactionType.LIKE,
            ReactionType.DISLIKE,
            ReactionType.HELPFUL,
            ReactionType.INSIGHTFUL,
        ]

        for i, reaction_type in enumerate(reaction_types):
            success = self.manager.add_reaction(
                comment.comment_id, f"user{i}", reaction_type
            )
            assert success

        reactions = self.manager.get_comment_reactions(comment.comment_id)
        assert len(reactions) == 4
        assert reactions["like"] == 1
        assert reactions["dislike"] == 1
        assert reactions["helpful"] == 1
        assert reactions["insightful"] == 1

    def test_comment_filtering_by_status(self):
        """Test filtering comments by status"""
        # Add active comment
        active_comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Active comment",
        )

        # Add and delete comment
        deleted_comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="To be deleted",
        )
        self.manager.delete_comment(deleted_comment.comment_id, "dr.researcher")

        # Get comments (should only return active)
        comments = self.manager.get_theory_comments("autism-theory-1", "1.0.0")
        assert len(comments) == 1
        assert comments[0].comment_id == active_comment.comment_id

        # Get comments including deleted
        all_comments = self.manager.get_theory_comments(
            "autism-theory-1", "1.0.0", include_deleted=True
        )
        assert len(all_comments) == 2

    def test_mention_extraction_edge_cases(self):
        """Test mention extraction with edge cases"""
        # Multiple mentions of same user
        comment = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="@dr.smith and @dr.smith again",
        )
        assert len(comment.mentions) == 1  # Should deduplicate

        # No mentions
        comment2 = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="No mentions in this comment",
        )
        assert len(comment2.mentions) == 0

        # Mentions with special characters
        comment3 = self.manager.add_comment(
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            author="dr.researcher",
            content="Email dr.smith@example.com is not a mention but @dr.smith is",
        )
        assert "dr.smith" in comment3.mentions
        assert len(comment3.mentions) == 1
