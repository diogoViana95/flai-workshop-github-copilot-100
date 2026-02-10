"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_participants = {
        name: activity["participants"].copy() 
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after each test
    for name, activity in activities.items():
        activity["participants"] = original_participants[name]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_activity_details(self, client):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        # Check Chess Club structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        # Verify data types
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity_success(self, client):
        """Test successful signup for an existing activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify student was added to participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_student_fails(self, client):
        """Test that signing up a student who is already registered fails"""
        # Sign up once
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Try to sign up again
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students_to_same_activity(self, client):
        """Test that multiple different students can sign up for the same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(f"/activities/Art Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students are registered
        activities_response = client.get("/activities")
        art_club = activities_response.json()["Art Club"]
        for email in emails:
            assert email in art_club["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_registered_student_success(self, client):
        """Test successful unregistration of a registered student"""
        # First sign up a student
        email = "test@mergington.edu"
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Programming Class/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Programming Class" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Programming Class"]["participants"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_unregistered_student_fails(self, client):
        """Test that unregistering a student who is not registered fails"""
        response = client.delete(
            "/activities/Soccer Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_preexisting_student_success(self, client):
        """Test unregistering a student that was pre-registered in the data"""
        # michael@mergington.edu is already in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify student was removed
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert "michael@mergington.edu" not in chess_club["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow of signing up and unregistering"""
        email = "workflow@mergington.edu"
        activity = "Science Club"
        
        # Initial state - student not registered
        activities_response = client.get("/activities")
        initial_participants = activities_response.json()[activity]["participants"]
        assert email not in initial_participants
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        after_signup = activities_response.json()[activity]["participants"]
        assert email in after_signup
        assert len(after_signup) == len(initial_participants) + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        final_participants = activities_response.json()[activity]["participants"]
        assert email not in final_participants
        assert len(final_participants) == len(initial_participants)
    
    def test_multiple_activities_per_student(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multisport@mergington.edu"
        activities_to_join = ["Soccer Club", "Track and Field", "Gym Class"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        all_activities = activities_response.json()
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
