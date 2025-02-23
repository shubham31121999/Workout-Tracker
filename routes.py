from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Workout

def init_routes(app):

    # Home Route
    @app.route('/')
    def home():
        return render_template('index.html')

    # User Registration
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            if User.query.filter_by(email=email).first():
                flash('Email already registered!', 'danger')
                return redirect(url_for('register'))

            # Create and save the new user
            user = User(username=username, email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    # User Login and JWT Token Generation (with Cookie)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()

            if not user or not user.check_password(password):
                flash('Invalid credentials!', 'danger')
                return redirect(url_for('login'))

            # Ensure user.id is converted to a string
            access_token = create_access_token(identity=str(user.id))

            flash('Login successful!', 'success')

            # Store JWT in a secure HttpOnly cookie
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite='Lax')

            return response

        return render_template('login.html')


    # User Dashboard (Protected Route)
    @app.route('/dashboard')
    @jwt_required(locations=["cookies"])
    def dashboard():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        return render_template('dashboard.html', username=user.username)

    # Manage Workouts (Create and List)
    @app.route('/workouts', methods=['GET', 'POST'])
    @jwt_required(locations=["cookies"])
    def workouts():
        current_user_id = get_jwt_identity()

        if request.method == 'POST':
            title = request.form['title']
            workout_date = request.form['date']

            # Create a new workout
            workout = Workout(title=title, date=workout_date, user_id=current_user_id)
            db.session.add(workout)
            db.session.commit()

            flash('Workout created!', 'success')
            return redirect(url_for('workouts'))

        # List the user's workouts
        user_workouts = Workout.query.filter_by(user_id=current_user_id).all()
        return render_template('workouts.html', workouts=user_workouts)

    # Workout Report (Summary)
    @app.route('/report')
    @jwt_required(locations=["cookies"])
    def report():
        current_user_id = get_jwt_identity()
        workouts = Workout.query.filter_by(user_id=current_user_id).all()
        return render_template('report.html', reports=workouts)

    # User Logout
    @app.route('/logout')
    def logout():
        flash('Logged out successfully!', 'success')
        
        # Clear JWT cookie on logout
        response = make_response(redirect(url_for('home')))
        response.delete_cookie('access_token')

        return response
