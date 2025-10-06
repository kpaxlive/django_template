#!/bin/bash

# Setup script for Django Authentication API
echo "🚀 Setting up Django Authentication API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your credentials"
fi

# Run migrations
echo "🗄️  Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "👤 Would you like to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Edit .env file with your OAuth credentials (optional)"
echo "   2. Run: python manage.py runserver"
echo "   3. Visit: http://localhost:8000/api/docs/"
echo ""
echo "🎉 Happy coding!"

