"""Tests for the Activities API endpoints."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # 9 initial activities
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_contains_required_fields(self, client):
        """Test that activities contain all required fields."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_list_structure(self, client):
        """Test that participants field contains a list of emails."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert isinstance(activity["participants"], list)
        assert len(activity["participants"]) == 2
        assert "michael@mergington.edu" in activity["participants"]
        assert "daniel@mergington.edu" in activity["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signing up adds a participant to an activity."""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added
        verify_response = client.get("/activities")
        activities = verify_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_increases_participant_count(self, client):
        """Test that signup increases the participant count."""
        activity_name = "Programming Class"
        email1 = "newstudent1@mergington.edu"
        email2 = "newstudent2@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Sign up first student
        client.post(f"/activities/{activity_name}/signup?email={email1}")
        
        # Sign up second student
        client.post(f"/activities/{activity_name}/signup?email={email2}")
        
        # Verify count increased
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        
        assert final_count == initial_count + 2

    def test_signup_to_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities."""
        email = "versatile@mergington.edu"
        
        # Sign up for two different activities
        client.post(f"/activities/Chess Club/signup?email={email}")
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Verify both signups
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Drama Club"]["participants"]


class TestUnregisterParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{participant_email} endpoint."""

    def test_unregister_removes_participant(self, client):
        """Test that deleting a participant removes them from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant exists before deletion
        initial_response = client.get("/activities")
        assert email in initial_response.json()[activity_name]["participants"]
        
        # Delete participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"] or "unregistered" in data["message"]
        
        # Verify participant was removed
        verify_response = client.get("/activities")
        assert email not in verify_response.json()[activity_name]["participants"]

    def test_unregister_decreases_participant_count(self, client):
        """Test that unregistering decreases the participant count."""
        activity_name = "Drama Club"
        email_to_remove = "isabella@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Unregister participant
        client.delete(f"/activities/{activity_name}/participants/{email_to_remove}")
        
        # Verify count decreased
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        
        assert final_count == initial_count - 1

    def test_unregister_all_participants(self, client):
        """Test that an activity can have all participants removed."""
        activity_name = "Basketball Team"
        
        # Get all participants
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"].copy()
        
        # Remove each participant
        for email in participants:
            client.delete(f"/activities/{activity_name}/participants/{email}")
        
        # Verify all removed
        final_response = client.get("/activities")
        assert len(final_response.json()[activity_name]["participants"]) == 0


class TestSignupErrors:
    """Tests for error cases in POST /activities/{activity_name}/signup."""

    def test_signup_to_nonexistent_activity_returns_404(self, client):
        """Test that signing up to a non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_signup_duplicate_participant_returns_400(self, client):
        """Test that signing up an existing participant returns 400."""
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Try to sign up someone who is already signed up
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already" in data["detail"].lower() or "duplicate" in data["detail"].lower()

class TestUnregisterErrors:
    """Tests for error cases in DELETE /activities/{activity_name}/participants/{participant_email}."""

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from a non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent Club/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_unregister_nonexistent_participant_returns_404(self, client):
        """Test that unregistering a non-existent participant returns 404."""
        response = client.delete(
            "/activities/Chess Club/participants/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_unregister_participant_not_in_activity_returns_404(self, client):
        """Test that unregistering someone not in an activity returns 404."""
        # emma is in Programming Class but not in Chess Club
        response = client.delete(
            "/activities/Chess Club/participants/emma@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestCombinedWorkflows:
    """Tests for workflows combining multiple operations."""

    def test_signup_then_unregister_workflow(self, client):
        """Test signing up and then unregistering."""
        activity_name = "Tennis Club"
        email = "workflow@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        check_response = client.get("/activities")
        assert email in check_response.json()[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity_name]["participants"]

    def test_multiple_signups_and_one_unregister(self, client):
        """Test multiple signups followed by selective unregister."""
        activity_name = "Robotics Club"
        email1 = "robot1@mergington.edu"
        email2 = "robot2@mergington.edu"
        email3 = "robot3@mergington.edu"
        
        # Sign up multiple students
        client.post(f"/activities/{activity_name}/signup?email={email1}")
        client.post(f"/activities/{activity_name}/signup?email={email2}")
        client.post(f"/activities/{activity_name}/signup?email={email3}")
        
        # Verify all are signed up
        check_response = client.get("/activities")
        participants = check_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        assert email3 in participants
        assert len(participants) == 5  # 2 initial + 3 new
        
        # Unregister one student
        client.delete(f"/activities/{activity_name}/participants/{email2}")
        
        # Verify only email2 was removed
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity_name]["participants"]
        assert email1 in final_participants
        assert email2 not in final_participants
        assert email3 in final_participants
        assert len(final_participants) == 4


class TestURLEncoding:
    """Tests for URL encoding handling in activity names with spaces."""

    def test_signup_with_url_encoded_activity_name(self, client):
        """Test that activity names with spaces are properly URL encoded."""
        # Chess Club has a space - should be properly encoded in URL
        email = "encoded@mergington.edu"
        
        # Using URL-encoded format (space as %20)
        response = client.post(
            "/activities/Chess%20Club/signup?email=" + email
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify it was added to the correct activity
        verify_response = client.get("/activities")
        assert email in verify_response.json()["Chess Club"]["participants"]

    def test_delete_with_url_encoded_activity_name(self, client):
        """Test that delete works with URL-encoded activity names."""
        activity_name = "Programming Class"  # Has space
        email = "newuser@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        # Then delete with URL encoding
        response = client.delete(
            f"/activities/Programming%20Class/participants/{email}"
        )
        
        assert response.status_code == 200
        
        # Verify participant was removed
        verify_response = client.get("/activities")
        assert email not in verify_response.json()[activity_name]["participants"]

    def test_url_encoded_email_in_delete(self, client):
        """Test that email addresses in URLs are properly handled."""
        activity_name = "Visual Arts"
        # The existing participant
        email = "ava@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        assert response.status_code == 200
        
        # Verify removal
        verify_response = client.get("/activities")
        assert email not in verify_response.json()[activity_name]["participants"]

    def test_all_activity_names_with_spaces_work_correctly(self, client):
        """Test that all activities with spaces in their names work correctly."""
        sp_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Visual Arts",
            "Robotics Club",
            "Debate Team"
        ]
        
        email = "testall@mergington.edu"
        
        # Try to sign up to each activity
        for activity in sp_activities:
            # URL encode the space
            encoded_name = activity.replace(" ", "%20")
            response = client.post(
                f"/activities/{encoded_name}/signup?email={email}"
            )
            
            # Should succeed or fail with 400 (duplicate) but not 404
            assert response.status_code in [200, 400], \
                f"Unexpected status for {activity}: {response.status_code}"
