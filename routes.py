from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, 
    set_access_cookies, unset_jwt_cookies
)
from models import db, User, Workout
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import create_access_token, set_access_cookies, get_csrf_token
from datetime import datetime
csrf = CSRFProtect()
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

            # ✅ Generate JWT token
            access_token = create_access_token(identity=str(user.id))

            # ✅ Get CSRF token from JWT
            csrf_token = get_csrf_token(access_token)

            # ✅ Store JWT & CSRF in secure cookies
            response = make_response(redirect(url_for('dashboard')))
            set_access_cookies(response, access_token)
            response.set_cookie("csrf_access_token", csrf_token, httponly=False, secure=True, samesite="Lax") 

            return response

        return render_template('login.html')

    # User Dashboard (Protected Route)
    @app.route('/dashboard')
    @jwt_required(locations=["cookies"])
    def dashboard():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        return render_template('dashboard.html', username=user.username)

    # @csrf.exempt  # ✅ Exempt this route from CSRF checks
    @app.route('/workouts', methods=['GET', 'POST'])
    @jwt_required(locations=["cookies"])
    def workouts():
        current_user_id = get_jwt_identity()

        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                title = data.get('title')
                workout_date = data.get('date')  # This is a string (YYYY-MM-DD)
            else:
                title = request.form.get('title')
                workout_date = request.form.get('date')

            if not title or not workout_date:
                return jsonify({"msg": "Missing title or date"}), 400

            try:
                # ✅ Convert the date string to a Python `date` object
                workout_date = datetime.strptime(workout_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"msg": "Invalid date format, use YYYY-MM-DD"}), 400

            # ✅ Save workout to database
            workout = Workout(title=title, date=workout_date, user_id=current_user_id)
            db.session.add(workout)
            db.session.commit()

            return jsonify({"msg": "Workout created successfully!"}), 201

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
        
        # ✅ Securely remove JWT cookies
        response = make_response(redirect(url_for('home')))
        unset_jwt_cookies(response)  

        return response
