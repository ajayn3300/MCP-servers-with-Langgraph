from mcp.server.fastmcp import FastMCP
import yfinance as yf

#intialize server
mcp = FastMCP('STOCKS')

#tools
@mcp.tool()
def get_stock_price(ticker: str) -> float | None:
    """
    Fetches the latest closing/current market price for a given ticker symbol.
    Example tickers: 'AAPL', 'MSFT', 'GOOGL', 'RELIANCE.NS' (for NSE India).
    """
    try:
        stock = yf.Ticker(ticker)
        # Fast retrieval via recent minute/day history
        data = stock.history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
        
        # Fallback to ticker info
        info = stock.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        return round(price, 2) if price else None

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Runs the server using standard input/output (stdio)
    mcp.run(transport="stdio")