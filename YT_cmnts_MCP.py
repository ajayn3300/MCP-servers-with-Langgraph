from youtube_comment_downloader import YoutubeCommentDownloader
from itertools import islice
from mcp.server.fastmcp import FastMCP

#intialize server
mcp = FastMCP('YT_CMNTS')

@mcp.tool()
def yt_cmnt_downloader(link: str) -> list:
    '''this function takes youtube link as an argument and return a list including maximum 250 comments on that video'''
    downloader = YoutubeCommentDownloader()
    comments = downloader.get_comments_from_url(link)
    comments = [comment['text'] for comment in islice(comments, 250)]
    return comments


if __name__ == "__main__":
    mcp.run(transport="stdio")