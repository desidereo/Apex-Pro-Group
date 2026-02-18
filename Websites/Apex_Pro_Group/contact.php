<?php
// Secure Contact Form Handler

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    
    // 1. Honeypot Check (Anti-Spam)
    // If the hidden 'website_url' field is filled, it's a bot.
    if (!empty($_POST["website_url"])) {
        die("System error. Please try again later."); 
    }

    // 2. Sanitize Inputs (Remove harmful characters)
    $name = strip_tags(trim($_POST["name"]));
    $email = filter_var(trim($_POST["email"]), FILTER_SANITIZE_EMAIL);
    $subject = strip_tags(trim($_POST["subject"]));
    $message = trim($_POST["message"]);

    // 3. Spam Keyword Filter
    $spam_keywords = [
        'seo service', 'web design', 'rank your website', 
        'improve your ranking', 'marketing proposal', 
        'viagra', 'casino', 'lottery', 'cryptocurrency investment scheme',
        'passive income from home', 'make money online'
    ];
    
    foreach ($spam_keywords as $keyword) {
        if (stripos($message, $keyword) !== false) {
            die("System error. Please try again later.");
        }
    }

    // 4. Link Count Check (More than 3 links is usually spam)
    if (substr_count($message, 'http') > 3 || substr_count($message, 'www.') > 3) {
         die("System error. Please try again later.");
    }

    // 5. Validate Inputs
    if (empty($name) || empty($message) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        // Redirect back with error (or handle via AJAX)
        header("Location: index.html?status=error");
        exit;
    }

    // 3. Email Configuration
    $recipient = "support@apexprogroup.uk"; // Your email
    $email_subject = "New Contact from Website: $subject";
    
    $email_content = "Name: $name\n";
    $email_content .= "Email: $email\n\n";
    $email_content .= "Message:\n$message\n";

    $email_headers = "From: Website Contact Form <noreply@apexprogroup.uk>\r\n";
    $email_headers .= "Reply-To: $email\r\n";
    $email_headers .= "X-Mailer: PHP/" . phpversion();

    // 4. Send Email
    if (mail($recipient, $email_subject, $email_content, $email_headers)) {
        // Success
        header("Location: index.html?status=success#contact-section");
    } else {
        // Server Error
        header("Location: index.html?status=server_error#contact-section");
    }

} else {
    // Not a POST request, redirect home
    header("Location: index.html");
}
?>