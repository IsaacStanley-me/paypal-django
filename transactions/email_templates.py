from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import base64
import os

# Load and encode the ICICI logo image as base64
logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'icici.png')
with open(logo_path, 'rb') as image_file:
    logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')


def construct_transfer_email(sender_name, receiver_name, receiver_email, amount, bank_name='ICICI BANK'):
    from datetime import datetime
    import pytz
    
    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%d %b %Y, %I:%M %p')
    
    subject = f'💰 Money Received: ₹{amount} from {sender_name.split()[0]} | ICICI Bank'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [receiver_email]

    html_content = f"""
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        body {{ font-family: 'Roboto', Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; padding: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #ff6b35, #ff9e1f); padding: 25px 20px; text-align: center; color: white; }}
        .logo {{ height: 50px; margin-bottom: 15px; }}
        .content {{ padding: 30px; color: #333333; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; font-size: 12px; color: #777777; text-align: center; border-top: 1px solid #eeeeee; }}
        .highlight {{ color: #ff6b35; font-weight: 500; }}
        .amount-box {{ 
            background-color: #fff8f2; 
            border-left: 4px solid #ff6b35;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }}
        .amount {{ 
            font-size: 24px; 
            font-weight: 700; 
            color: #333;
            margin: 5px 0;
        }}
        .details-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        .details-table td {{ 
            padding: 10px 0; 
            border-bottom: 1px solid #eee;
        }}
        .details-table td:first-child {{ 
            color: #666;
            width: 40%;
        }}
        .button {{ 
            display: inline-block; 
            background: #ff6b35; 
            color: white; 
            padding: 12px 25px; 
            text-decoration: none; 
            border-radius: 4px; 
            font-weight: 500;
            margin: 10px 0;
        }}
        .button:hover {{ 
            background: #e05d2d;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="data:image/png;base64,{logo_base64}" alt="ICICI Bank Logo" class="logo" />
                <h2 style="margin: 10px 0 0; font-weight: 500;">Money Received</h2>
            </div>
            <div class="content">
                <p>Dear <span class="highlight">{receiver_name}</span>,</p>
                <p>We're pleased to inform you that you've received a payment.</p>
                
                <div class="amount-box">
                    <div style="font-size: 14px; color: #666;">Amount Received</div>
                    <div class="highlight amount">₹{amount}</div>
                    <div style="font-size: 14px; color: #666;">Transaction completed on {current_time} (IST)</div>
                </div>

                <table class="details-table">
                    <tr>
                        <td>From Account</td>
                        <td><strong>{sender_name}</strong></td>
                    </tr>
                    <tr>
                        <td>To Account</td>
                        <td><strong>{receiver_name}</strong></td>
                    </tr>
                    <tr>
                        <td>Transaction Reference</td>
                        <td><strong>ICICI{datetime.now().strftime('%Y%m%d%H%M%S')}</strong></td>
                    </tr>
                    <tr>
                        <td>Bank</td>
                        <td><strong>{bank_name}</strong></td>
                    </tr>
                </table>

                <p style="margin-top: 25px;">The amount has been credited to your account and is available for use.</p>
                
                <div style="text-align: center; margin: 30px 0 20px;">
                    <a href="#" class="button">View Transaction Details</a>
                </div>
                
                <p style="font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
                    <strong>Note:</strong> This is an auto-generated email. Please do not reply to this email.
                </p>
            </div>
            <div class="footer">
                <p>© 2025 ICICI Bank Ltd. All rights reserved.</p>
                <p>ICICI Bank Ltd., ICICI Bank Towers, Bandra-Kurla Complex, Mumbai - 400051, India</p>
                <p style="margin-top: 10px;">
                    <a href="#" style="color: #ff6b35; text-decoration: none; margin: 0 10px;">Security</a> | 
                    <a href="#" style="color: #ff6b35; text-decoration: none; margin: 0 10px;">Privacy Policy</a> | 
                    <a href="#" style="color: #ff6b35; text-decoration: none; margin: 0 10px;">Terms & Conditions</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, '', from_email, to)
    msg.attach_alternative(html_content, "text/html")
    return msg
