# Postman Collection for Social Network API

This directory contains a complete Postman collection for testing the Social Network API.

## Files

- `postman_collection.json` - The main Postman collection with all API endpoints
- `postman_environment.json` - Environment variables for local development

## Import Instructions

### Import Collection

1. Open Postman
2. Click **Import** button in the top left
3. Select the `postman_collection.json` file
4. Click **Import**

### Import Environment

1. In Postman, click the **Environments** icon (gear icon) in the top right
2. Click **Import**
3. Select the `postman_environment.json` file
4. Click **Import**
5. Select "Social Network API - Local" from the environment dropdown

## Collection Structure

The collection is organized into the following folders:

### 1. Health
- **Liveness Check** - Check if the API is alive
- **Readiness Check** - Check if the API is ready to serve requests

### 2. Authentication
- **Register User** - Create a new user account (saves access and refresh tokens automatically)
- **Login** - Authenticate with username and password (saves tokens automatically)
- **Refresh Token** - Get new access token using refresh token (saves new tokens automatically)

### 3. Users
- **Get My Profile** - Retrieve the authenticated user's profile (saves userId automatically)
- **Update My Profile** - Update the authenticated user's profile information
- **Get User By ID** - Retrieve a specific user's public profile
- **Search Users** - Search for users by query string

### 4. Posts
- **Create Post** - Create a new post (saves postId automatically)
- **Get Post By ID** - Retrieve a specific post
- **List Posts** - List all posts with pagination
- **List Posts By Author** - List posts filtered by author
- **Delete Post** - Delete a post (must be owner or admin)
- **Like Post** - Like a post
- **Unlike Post** - Remove like from a post
- **Get Like Count** - Get the number of likes for a post

### 5. Comments
- **Add Comment to Post** - Add a comment to a post (saves commentId automatically)
- **List Comments for Post** - List all comments for a specific post
- **Delete Comment** - Delete a comment (must be owner or admin)

### 6. Follows
- **Follow User** - Follow a user
- **Unfollow User** - Unfollow a user
- **List Followers** - Get list of user's followers
- **List Following** - Get list of users that a user is following

### 7. Feed
- **Get User Feed** - Get personalized feed of posts from followed users

## Environment Variables

The collection uses the following variables:

- `baseUrl` - Base URL of the API (default: http://localhost:8000)
- `accessToken` - JWT access token (auto-populated after login/register)
- `refreshToken` - JWT refresh token (auto-populated after login/register)
- `userId` - User ID (auto-populated after getting profile)
- `postId` - Post ID (auto-populated after creating a post)
- `commentId` - Comment ID (auto-populated after creating a comment)

## Usage Guide

### Quick Start

1. **Start the API**: Make sure your API is running on `http://localhost:8000`

2. **Health Check**: Run the "Liveness Check" request to verify the API is running

3. **Register a User**: 
   - Open "Authentication" folder
   - Run "Register User" request
   - Tokens will be automatically saved

4. **Create a Post**:
   - Open "Posts" folder
   - Run "Create Post" request
   - The postId will be automatically saved

5. **Explore**: Try other endpoints using the saved variables

### Authentication Flow

Most endpoints require authentication. The collection handles this automatically:

1. Register or Login first
2. Access and refresh tokens are automatically saved to collection variables
3. Protected endpoints include the Authorization header: `Bearer {{accessToken}}`
4. When the access token expires, use the "Refresh Token" request

### Testing Different Users

To test interactions between users:

1. Create a first user account (Register)
2. Note the tokens and userId
3. Create a second user account:
   - Change the username and email in Register request
   - Run Register again
4. Now you can test follow/unfollow between the two users

### Testing Workflow Example

Here's a complete workflow to test the main features:

1. **Setup**
   - Run "Register User" (creates User A)
   - Save User A's tokens
   
2. **Create Content**
   - Run "Create Post" (User A creates a post)
   - Run "Add Comment to Post" (User A comments on their post)
   
3. **Register Second User**
   - Modify and run "Register User" again (creates User B)
   - User B's tokens are now active
   
4. **Interact as User B**
   - Run "Follow User" with User A's ID
   - Run "Like Post" on User A's post
   - Run "Add Comment to Post" on User A's post
   
5. **Check Feed**
   - Run "Get User Feed" (User B sees User A's posts)
   
6. **Switch Back to User A**
   - Manually set accessToken to User A's token
   - Run "List Followers" to see User B
   - Run "Get Post By ID" to see likes and comments

## API Documentation

For detailed API documentation, you can:

1. Start the API server
2. Visit `http://localhost:8000/docs` for interactive Swagger documentation
3. Visit `http://localhost:8000/redoc` for ReDoc documentation

## Troubleshooting

### Authentication Errors (401)

- Check that you've run "Register User" or "Login" first
- Verify the `accessToken` variable is set
- If token expired, run "Refresh Token"

### Not Found Errors (404)

- Verify the resource ID variables are set correctly
- Check that the resource was created successfully

### Rate Limiting (429)

- The API has rate limiting enabled
- Wait a moment before retrying
- Check the retry-after header in the response

### Connection Errors

- Verify the API is running: `http://localhost:8000/health/liveness`
- Check the `baseUrl` environment variable is correct
- Verify Docker containers are up if using Docker

## Advanced Usage

### Running the Entire Collection

You can run all requests in sequence using Postman's Collection Runner:

1. Click on the collection name
2. Click "Run" button
3. Select "Social Network API - Local" environment
4. Click "Run Social Network API"

Note: Some requests may fail if they depend on previous requests' data.

### Exporting Test Results

1. Run the collection using Collection Runner
2. Click "Export Results" after completion
3. Save the results for documentation or debugging

### Creating Additional Environments

To test against different environments (staging, production):

1. Duplicate the environment
2. Rename it (e.g., "Social Network API - Staging")
3. Update the `baseUrl` to point to your staging/production server
4. Switch environments using the dropdown

## Contributing

When adding new endpoints to the API:

1. Add corresponding requests to the collection
2. Use appropriate folders for organization
3. Add test scripts to auto-save important IDs
4. Update this README with the new endpoints
5. Include example request bodies

## Notes

- All timestamps are in ISO 8601 format
- UUIDs are used for all resource IDs
- Passwords must be at least 8 characters
- Post content is limited to 280 characters
- Default pagination size is 20, maximum is 100

