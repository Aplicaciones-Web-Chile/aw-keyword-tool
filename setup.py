from setuptools import setup, find_packages

setup(
    name="keyword_idea_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Flask==3.0.1",
        "requests==2.31.0",
        "beautifulsoup4==4.12.3",
        "python-dotenv==1.0.1",
        "pytrends==4.9.2",
        "lxml==5.1.0",
    ],
    python_requires=">=3.8",
)
