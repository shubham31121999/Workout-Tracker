from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, 
    set_access_cookies, unset_jwt_cookies
)
from models import db, User, Workout,Goal
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
            try:
                # Extract workout data
                data = request.get_json()
                title = data.get('title')
                date = data.get('date')
                duration = data.get('duration')
                calories_burned = data.get('calories_burned')
                workout_type = data.get('workout_type')
                intensity = data.get('intensity')
                notes = data.get('notes')

                # Validate required fields
                if not all([title, date, duration]):
                    return jsonify({'error': 'Missing required fields'}), 400

                # Parse date and convert values
                date = datetime.strptime(date, '%Y-%m-%d').date()
                duration = int(duration)
                calories_burned = int(calories_burned) if calories_burned else None

                # Create and save new workout
                new_workout = Workout(
                    title=title,
                    date=date,
                    duration=duration,
                    calories_burned=calories_burned,
                    workout_type=workout_type,
                    intensity=intensity,
                    notes=notes,
                    user_id=current_user_id
                )

                db.session.add(new_workout)
                db.session.commit()

                # Update user's goals based on the new workout
                update_goals(current_user_id, new_workout)

                return jsonify({'message': 'Workout added successfully'}), 201

            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': 'Internal Server Error'}), 500

        # GET: Retrieve and display workout history
        user_workouts = Workout.query.filter_by(user_id=current_user_id).order_by(Workout.date.desc()).all()
        return render_template('workouts.html', workouts=user_workouts)

    
    
    
    @app.route('/goals', methods=['GET', 'POST'])
    @jwt_required(locations=["cookies"])
    def goals():
        current_user_id = get_jwt_identity()

        if request.method == 'POST':
            data = request.get_json()
            goal_type = data.get('goal_type')  # 'Calories', 'Duration', 'Frequency'
            target_value = int(data.get('target_value'))
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

            new_goal = Goal(
                user_id=current_user_id,
                goal_type=goal_type,
                target_value=target_value,
                end_date=end_date
            )

            db.session.add(new_goal)
            db.session.commit()
            return jsonify({'message': 'Goal created successfully!'}), 201

        user_goals = Goal.query.filter_by(user_id=current_user_id).all()
        return render_template('goals.html', goals=user_goals)

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
    
    
    def update_goals(user_id, workout):
    # Fetch active goals for the logged-in user
        active_goals = Goal.query.filter_by(user_id=user_id, status="In Progress").all()

        for goal in active_goals:
            if goal.goal_type == "Calories" and workout.calories_burned:
                goal.current_value += workout.calories_burned

            elif goal.goal_type == "Duration":
                goal.current_value += workout.duration

            elif goal.goal_type == "Frequency":
                goal.current_value += 1

            # Mark goal as completed if target is reached
            if goal.current_value >= goal.target_value:
                goal.status = "Completed"

        db.session.commit()

