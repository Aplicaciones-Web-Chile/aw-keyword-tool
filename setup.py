from setuptools import setup, find_packages

setup(
    name="keyword_idea_generator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask>=2.0.1',
        'requests>=2.26.0',
        'beautifulsoup4>=4.10.0',
        'python-dotenv>=0.19.0',
        'pandas>=1.3.4',
        'flask-caching>=1.10.1',
        'flask-login>=0.5.0',
        'flask-socketio>=5.3.6',
        'python-socketio>=5.0.2',
        'eventlet>=0.33.3',
        'pytrends>=4.9.2',
        'lxml>=4.9.0'
    ],
    entry_points={
        'console_scripts': [
            'run-app=keyword_idea_generator.app:create_app'
        ]
    }
)