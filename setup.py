from setuptools import setup, find_packages

setup(
    name="keyword_idea_generator",
    version="0.1",
    packages=find_packages(where="keyword_idea_generator"),
    package_dir={"": "keyword_idea_generator"},
    install_requires=[
        'Flask>=2.0.1',
        'requests>=2.26.0',
        'beautifulsoup4>=4.10.0',
        'python-dotenv>=0.19.0',
        'pandas>=1.3.4',
        'flask-caching>=1.10.1',
        'flask-login>=0.5.0'
    ],
    entry_points={
        'console_scripts': [
            'run-app=keyword_idea_generator.app:main'
        ]
    }
)