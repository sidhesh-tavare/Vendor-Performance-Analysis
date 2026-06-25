import sqlite3
import logging
import pandas as pd

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)


def create_vendor_summary(conn):

    query = """
    WITH FreightSummary AS (
        SELECT
            VendorNumber,
            SUM(Freight) AS FreightCost
        FROM vendor_invoice
        GROUP BY VendorNumber
    ),

    PurchaseSummary AS (
        SELECT
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price AS ActualPrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
        WHERE p.PurchasePrice > 0
        GROUP BY
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price,
            pp.Volume
    ),

    SalesSummary AS (
        SELECT
            VendorNo,
            Brand,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
        FROM sales
        GROUP BY
            VendorNo,
            Brand
    )

    SELECT
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,

        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,

        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,

        fs.FreightCost

    FROM PurchaseSummary ps

    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNo
       AND ps.Brand = ss.Brand

    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber

    ORDER BY
        ps.TotalPurchaseDollars DESC
    """

    return pd.read_sql_query(query, conn)


def clean_data(df):

    df["Volume"] = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    )

    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(0)

    df["VendorName"] = df["VendorName"].str.strip()

    df["GrossProfit"] = (
        df["TotalSalesDollars"]
        - df["TotalPurchaseDollars"]
    )

    df["ProfitMargin"] = (
        df["GrossProfit"]
        / df["TotalSalesDollars"]
    ) * 100

    df["StockTurnover"] = (
        df["TotalSalesQuantity"]
        / df["TotalPurchaseQuantity"]
    )

    df["SalesToPurchaseRatio"] = (
        df["TotalSalesDollars"]
        / df["TotalPurchaseDollars"]
    )

    df["NetProfit"] = (
        df["TotalSalesDollars"]
        - df["TotalPurchaseDollars"]
        - df["FreightCost"]
    )

    df["AvgBuyPrice"] = (
        df["TotalPurchaseDollars"]
        / df["TotalPurchaseQuantity"]
    )

    df["AvgSellPrice"] = (
        df["TotalSalesDollars"]
        / df["TotalSalesQuantity"]
    )

    df["PriceDifference"] = (
        df["AvgSellPrice"]
        - df["AvgBuyPrice"]
    )

    df["PriceDifferencePct"] = (
        df["PriceDifference"]
        / df["AvgBuyPrice"]
    ) * 100

    return df


if __name__ == "__main__":

    conn = sqlite3.connect("inventory.db")

    logging.info("Creating Vendor Summary")

    vendor_sales_summary = create_vendor_summary(conn)

    logging.info(
        f"Rows: {len(vendor_sales_summary):,}"
    )

    logging.info("Cleaning Data")

    vendor_sales_summary = clean_data(
        vendor_sales_summary
    )

    logging.info("Saving Table")

    vendor_sales_summary.to_sql(
        "vendor_sales_summary",
        conn,
        if_exists="replace",
        index=False
    )

    logging.info("Completed")

    conn.close()