import os
from github import Github, Auth
from dotenv import load_dotenv
load_dotenv()
from mcp.server.fastmcp import FastMCP

#intialize server
mcp = FastMCP('GITHUB')

@mcp.tool()
def extract_content(repo_link :str) ->dict:

    '''this function takes github repository link as an argument and return all the python releated content with their file names as a dictionery'''
    link = repo_link.replace("https://github.com/",'')

    # Retrieve the token
    token = os.getenv("GITHUB_API_KEY")

    #gitub
    git = Github(auth = Auth.Token(token))

    #getting repo
    repo = git.get_repo(link)

    # extracting only code content
    contents = [i for i in repo.get_contents('') if i.name.endswith(('py','ipynb'))]

    data = {file.name:file.decoded_content.decode("utf-8") for file in contents}
    return data



if __name__ == "__main__":
    # Runs the server using standard input/output (stdio)
    mcp.run(transport="stdio")


