from flask import Flask, render_template, request, redirect, url_for, session, flash
import statistics
import os

app = Flask(__name__)

os.urandom(24)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_key_if_not_found')

#route handler: displays different messages based on user authentication
@app.route('/')
def home():
    #log in: welcome message with the user's name and a logout link
    if 'username' in session: 
        return f'Welcome {session["username"]}! <a href="/logout">Logout</a>'
    
    #display a message with links to the login and registration pages
    return 'You are not logged in <a href="/login">Login</a> <a href="/register">Register</a>'

users = {} #store user information (dictionary)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        t = request.form['t'] 
        users[username] = {'password': password, 'timings': t} 
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

def check_timings(registered_timings, login_timings, tolerance=0.3, outlier_tolerance=2):
    if not registered_timings or not login_timings:
        print("Error: Timing data is missing.")
        return False

    #convert the comma-separated string of timings into a list of floats
    registered = [float(time) for time in registered_timings.split(',') if time.strip()]
    login = [float(time) for time in login_timings.split(',') if time.strip()]

    # number of timing events: registration matches login
    if len(registered) != len(login):
        print("Mismatch in data length")
        return False

    #calculate the mean and standard deviation of the registered timings
    mean_registered = statistics.mean(registered)
    std_dev_registered = statistics.stdev(registered)

    #create a list of the absolute relative differences between registered and login timings
    filtered_differences = [
        abs((r - l) / r) for r, l in zip(registered, login)
        if abs(r - mean_registered) <= outlier_tolerance * std_dev_registered
    ]

    #Calculate the average of the filtered differences; 
    #validation: the average difference is within the acceptable 'tolerance'
    avg_difference = statistics.mean(filtered_differences) if filtered_differences else 0
    print(f"Filtered Average difference: {avg_difference:.2f}")
    
    return avg_difference <= tolerance, registered_timings, login_timings

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_timings = request.form['t'] 
        print(f"Logging in with username: {username}, password: {password}, timings: {login_timings}")

        user = users.get(username)
        if user:
            if user['password'] == password:
                if check_timings(user['timings'], login_timings):
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('User login failed due to keystroke dynamics failure', 'error')
            else:
                flash('Invalid password', 'error')
        else:
            flash('User not found', 'error')

        print("Login failed, redirecting back to login page.")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
