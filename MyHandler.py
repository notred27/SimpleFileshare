import http.server
from http.cookies import SimpleCookie
import os
import urllib.parse
import cgi

# Test login info (TO BE CHECKED AGAINST HASHED PASSWORDS IN THE FUTURE)
USERNAME = "admin"
PASSWORD = "password"



# Paths to HTML files to display
LOGIN_HTML_PATH = os.path.join(os.getcwd(), 'login.html')
DEFAULT_HTML_PATH = os.path.join(os.getcwd(), 'default.html')

# Path to desktop (Base directory)
desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')


# Load base HTML so it can be displayed from other directories
base_html= ""
try:
    with open(DEFAULT_HTML_PATH, 'r') as file:
        base_html= file.read()

except FileNotFoundError as e:
    print(e)



# Creating a HTTP request handler
class MyHandler(http.server.SimpleHTTPRequestHandler):

    # Handel HTTP GET requests
    def do_GET(self):
        # Send to "/login" or redirect to desktop ("/")
        if self.path == "/login":
            if not self.is_authenticated():
                # Serve the login page until authenticated
                self.serve_login_page()  
            else:
                # Redirect to main dir
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            return
        
        # Redirect to "/login" if auth cookie isn't found, or if "/logout" is visited
        if not self.is_authenticated() or self.path == "/logout":
            self.redirect_to_login()
            return
 
        
        # Otherwise, must be in the server and either viewing a directory or file
        self.serve_directory_listing(self.path)


    # Handel HTTP POST requests for the server 
    def do_POST(self):
        
        if self.path == "/login":
            # Get the client's username and password from the posted form
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = urllib.parse.parse_qs(post_data)

  
            if self.valid_login(form_data):
                # Valid credentials, send cookie and redirect
                self.redirect_to_main()
            else:
                # Invalid credentials, show error on login page 
                self.serve_login_page(failed_signin=True)
                return
            

        elif self.path == "/logout":
            # Clear auth cookie and return to the login page
            self.redirect_to_login()
            return
        
        else:
            # Handle any other POST request (i.e. file uploads)

            try:
                # Read file data from form
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE':self.headers['Content-Type']}
                )

                # Get filename and data
                filename = form['shared_file'].filename
                data = form['shared_file'].file.read()

                with open(f"./uploaded_{filename}", 'wb') as f:
                    f.write(data)  # Save the file content to disk


                # Send Confirmation
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"File upload successful")

            except:
                # Send error
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"An unexpected error occurred.")




    def is_authenticated(self):
        # Check for the authentication cookie
        cookies = self.headers.get('Cookie')
        if cookies:
            cookie = SimpleCookie(cookies)
            return cookie.get("authenticated") and cookie["authenticated"].value == "true"
        return False
    

    def valid_login(self, form):
        # TODO: Improve this to use something other than plaintext credentials
        username = form.get('username', [None])[0]
        password = form.get('password', [None])[0]

        # Check if credentials are correct
        return username == USERNAME and password == PASSWORD


    def serve_login_page(self, failed_signin = False):
        # Serve HTML file for the login page
        try:
            with open(LOGIN_HTML_PATH, 'r') as file:
                login_page = file.read()

            # If the sign-in credentials failed, show a pop-up error (on the page)
            if failed_signin:
                login_page = login_page.replace(
                    "</body>",
                    """
                    <div id="login-fail-modal" style="display:block; z-index:4; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0, 0, 0, 0.5); text-align:center; padding-top:30vh;">
                        <div style="background-color:#4A051C; color:#FDE8E9; padding:20px; border-radius:5px; width:300px; margin:auto;">
                            <h3>Login Failed</h3>
                            <p>Invalid username or password. Please try again.</p>
                            <button onclick="document.getElementById('login-fail-modal').style.display='none'">Close</button>
                        </div>
                    </div>
                    </body>
                    """
                )

            # Send the HTML content to the client w/ OK header
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-store')  # Prevent caching (for cookie)
            self.send_header('Pragma', 'no-cache')  # For HTTP/1.0 compatibility
            self.send_header('Expires', '0')  # Expiry immediately
            self.end_headers()
            self.wfile.write(login_page.encode())

        except FileNotFoundError:
            # If the login.html file is not found, send an error message
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Login page not found!</h2></body></html>")


    def redirect_to_login(self):
        # Redirect to login
        self.send_response(302)
        self.send_header('Location', '/login')  

        # Expire cookie
        cookie = SimpleCookie()
        cookie["authenticated"] = ""
        cookie["authenticated"]["path"] = "/"
        cookie["authenticated"]["max-age"] = 0  # Expiry immediately
        
        # Prevent storing the cookie
        self.send_header("Set-Cookie", cookie.output(header="", sep=""))
        self.send_header('Cache-Control', 'no-store')  # Prevent caching
        self.send_header('Pragma', 'no-cache')  # For HTTP/1.0 compatibility
        self.send_header('Expires', '0')  # Expiry immediately
        self.end_headers()
        return
    

    def redirect_to_main(self):
        # Create auth cookie if credentials are valid, and redirect to main dir "/"
        self.send_response(302)  
        self.send_header('Location', '/') 

        # Create auth cookie
        cookie = SimpleCookie()
        cookie["authenticated"] = "true"
        cookie["authenticated"]["path"] = "/"
        cookie["authenticated"]["max-age"] = 600  # Cookie expires after 10 minutes
        cookie["authenticated"]["secure"] = True   # Secure flag (cookie is only sent over HTTPS)
        cookie["authenticated"]["httponly"] = True # HttpOnly flag (cookie can't be accessed via JavaScript)
        cookie["authenticated"]["samesite"] = "Strict"  # Prevents cross-site request forgery

        self.send_header("Set-Cookie", cookie.output(header="", sep=""))
        self.end_headers()




    def serve_directory_listing(self, dir_path):
        """Serve an HTML page that lists the contents of the given directory."""
        try:            
            # Decode the current URL path
            dir_path = urllib.parse.unquote(dir_path)

            # Ensure the path is an absolute path
            abs_path = os.path.abspath(os.path.join(desktop, dir_path.lstrip('/')))  # Join URL path to base directory


            # Restrict access to within the BASE_DIR to prevent path traversal vulnerabilities
            if not os.path.commonpath([abs_path, desktop]) == desktop:
                # This prevents users from accessing outside the base directory (path traversal attack)
                self.send_response(403)  # Forbidden
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h2>Forbidden: You don't have permission to access this directory!</h2></body></html>")
                return


            # Open this if the path points to a file
            if os.path.isfile(abs_path):
                super().do_GET()
                return


            # List the files in the directory
            if not os.path.isdir(abs_path):
                self.send_response(404)  # Not found
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h2>Directory not found! :(</h2></body></html>")
                return
            
            # Get all of the files in the current directory
            files = os.listdir(abs_path)

            default_page = self.create_listing_html(files, dir_path)

            # Send the OK response headers and content
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-store')  # Prevent caching
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            self.wfile.write(default_page.encode())  # Send the directory listing HTML


        except PermissionError:
            # If there's a permission issue, return a 403 Forbidden error
            self.send_response(403)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Permission denied!</h2></body></html>")


    def create_listing_html(self, files, dir_path):
        # Add custom HTML for the directory listing

        # Sorted alphabetically, with files listed first then directories
        rows = []
        file_count = 0
        for file in files:

            # Calculate relative path of each file
            if dir_path != "/":
                pth = dir_path.lstrip('/') + "/" + file+ "/"
            else:
                pth = file

            html = "<div class=\"grid_row\">"
            if os.path.isdir(pth):
                # This is a directory
                file_link = f'<span class = \"filename\"><a href="/{pth}">{file}</a></span><span>Dir</span><span></span>' 
                html += file_link + "</div>"
                rows.append(html)
     
            else:
                # This is some kind of file
                pth = pth.rstrip("/")
                try:
                    file_link = f'<span class = \"filename\"><a href="/{pth}">{file}</a></span><span>File</span><span>{format_size(os.path.getsize(pth))}</span>'
                except:
                    file_link = f'<span class = \"filename\"><a href="/{pth}">{file}</a></span><span>File</span><span>?</span>'

                html += file_link + "</div>"
                rows.insert(file_count, html)
                file_count += 1

        html = "".join(rows)

        # Add this HTML to the base file contents
        return base_html.replace("</body>", f"{html}</body>")



















def format_size(size_bytes):
    """
    Format size in bytes into a human-readable format (e.g., KB, MB, GB)
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"



