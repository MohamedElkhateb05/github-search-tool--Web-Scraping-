GitHub Repository Search Tool 🔎
A Python script to search GitHub repositories and save the results in various file formats. This tool helps you find and collect data on projects by stars, language, or other criteria, with support for pagination and API rate limit handling.

✨ Features
Powerful Search: Query GitHub for repositories based on keywords, minimum stars, and language.

Flexible Output: Save search results in JSON, CSV, TSV, or XML formats.

Translation Support: Automatically translates repository descriptions that are not in English or Arabic.

Interactive Prompts: Simple command-line interface that asks you for the search term, file format, and filename.

GitHub Token Support: Use a personal access token to increase the API rate limit from 60 to 5,000 requests per hour for more extensive searches.

🚀 How to Use
Prerequisites
Before running the script, you'll need to install the necessary Python libraries.

pip install requests langdetect

Note: The urllib3 library is a dependency of requests and will be installed automatically.

Running the Script
Run the script from your terminal:

python github_search_tool.py

Follow the on-screen prompts to enter your search term, select the file format, and provide a filename.

Using a GitHub Token (Optional)
For large-scale searches, it is highly recommended to use a GitHub Personal Access Token.

Create a token with the public_repo scope on your GitHub account.

Set it as an environment variable named GITHUB_TOKEN:

macOS/Linux: export GITHUB_TOKEN="your_token_here"

Windows: set GITHUB_TOKEN="your_token_here"

Alternatively, you can pass the token directly as a command-line argument:

python github_search_tool.py --token your_token_here

📝 File Formats
The script offers four output formats, each with a different use case:

Format

Description

Use Case

JSON

Stores data in a human-readable, structured format.

Best for general-purpose data exchange and use in other applications.

CSV

Plain-text format where data is separated by commas.

Ideal for opening and analyzing data in spreadsheet applications like Microsoft Excel.

TSV

Similar to CSV, but uses tabs as delimiters.

Useful when data fields might contain commas, preventing parsing errors.

XML

A markup language with a structured, hierarchical format.

Common in older systems and web services for data transmission.

⚖️ License
This project is licensed under the MIT License. See the LICENSE file for details.
