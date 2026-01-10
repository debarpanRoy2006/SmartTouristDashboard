# In a real-world application, you would use a service like Twilio for SMS
# and SendGrid/Mailgun for emails. For now, we'll print to the console.

def send_email_otp(email, otp):
    """
    Simulates sending an OTP to the user's email.
    In production, integrate a real email service here.
    """
    subject = "Your Verification Code for Smart Tourist Safety System"
    message = f"Your One-Time Password (OTP) is: {otp}"
    print("--- SIMULATING EMAIL ---")
    print(f"To: {email}")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print("------------------------")
    return True

def send_phone_otp(phone_number, otp):
    """
    Simulates sending an OTP to the user's phone number via SMS.
    In production, integrate a real SMS gateway like Twilio here.
    """
    message = f"Your Smart Tourist Safety System verification code is: {otp}"
    print("--- SIMULATING SMS ---")
    print(f"To: {phone_number}")
    print(f"Message: {message}")
    print("----------------------")
    return True
