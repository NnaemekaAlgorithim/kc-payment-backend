#!/bin/bash

# Configuration
PROJECT_DIR="/home/$USER/kc-payment-backend"
VENV_PATH="$PROJECT_DIR/venv"
REPO_URL="https://github.com/NnaemekaAlgorithim/kc-payment-backend.git"  # Replace with your repo URL
BRANCH="main"  # Replace with your branch name
GUNICORN_SERVICE="payment_gunicorn"  # Adjusted to match the service name
NGINX_SERVICE="nginx"

# Exit on any error
set -e

echo "Starting deployment process for payment..."

# Step 1: Ensure PostgreSQL dependencies
echo "Installing PostgreSQL dependencies..."
sudo apt update
sudo apt install -y libpq-dev python3-dev

# Step 2: Navigate to project directory
cd "$PROJECT_DIR" || { echo "Failed to navigate to $PROJECT_DIR"; exit 1; }

# Step 3: Pull updates from Git
echo "Pulling updates from Git repository..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH" || { echo "Git pull failed"; exit 1; }

# Step 4: Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate" || { echo "Failed to activate virtual environment"; exit 1; }

# Step 5: Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
cd payment
pip install -r ../requirements.txt || { echo "Failed to install requirements"; exit 1; }

# Step 6: Run migrations
echo "Running Django migrations..."
python manage.py makemigrations || { echo "Makemigrations failed"; exit 1; }
python manage.py migrate || { echo "Migrate failed"; exit 1; }

# Step 7: Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || { echo "Collectstatic failed"; exit 1; }

# Step 8: Set permissions for static files and socket
echo "Setting permissions..."
sudo chown -R $USER:www-data "$PROJECT_DIR/staticfiles"
sudo chmod -R 755 "$PROJECT_DIR/staticfiles"
sudo chown $USER:www-data "$PROJECT_DIR/gunicorn.sock"
sudo chmod 660 "$PROJECT_DIR/gunicorn.sock"

# Step 9: Ensure Redis is installed and running
echo "Installing and starting Redis..."
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server --no-pager

# Step 10: Restart Gunicorn and Nginx
echo "Restarting Gunicorn and Nginx..."
sudo systemctl restart "$GUNICORN_SERVICE" || { echo "Failed to restart Gunicorn"; exit 1; }
sudo systemctl restart "$NGINX_SERVICE" || { echo "Failed to restart Nginx"; exit 1; }

# Step 11: Verify services
echo "Checking service status..."
sudo systemctl status "$GUNICORN_SERVICE" --no-pager
sudo systemctl status "$NGINX_SERVICE" --no-pager

echo "Deployment completed successfully for payment!"
