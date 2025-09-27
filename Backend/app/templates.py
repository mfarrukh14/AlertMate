"""HTML templates for the AlertMate frontend - DEPRECATED.
All frontend functionality has been moved to React components in Frontend/src/components/"""

# This file is kept for backward compatibility but should not be used
# All HTML/CSS has been moved to proper React components

def get_login_signup_page() -> str:
    """DEPRECATED: Use React AuthPage component instead."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AlertMate - Deprecated Template</title>
</head>
<body>
    <h1>This template has been moved to React</h1>
    <p>Please use the React frontend at /auth</p>
</body>
</html>
"""

def get_chat_page() -> str:
    """DEPRECATED: Use React ChatPage component instead.""" 
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AlertMate - Deprecated Template</title>
</head>
<body>
    <h1>This template has been moved to React</h1>
    <p>Please use the React frontend at /chat</p>
</body>
</html>
"""

def get_admin_dashboard() -> str:
    """DEPRECATED: Use React AdminDashboard component instead."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AlertMate - Deprecated Template</title>
</head>
<body>
    <h1>This template has been moved to React</h1>
    <p>Please use the React frontend at /admin</p>
</body>
</html>
"""