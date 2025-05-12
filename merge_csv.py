import os
import argparse
import sys
import pandas as pd
from pandas.api.types import is_float_dtype
from pandas.core.api import DataFrame
import glob
from datetime import datetime


def canon_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y/%m/%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(d, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    raise ValueError("unsupported date format: {}".format(d))


def clean_date_column(df: pd.DataFrame, column: str):
    d = pd.to_datetime(df[column], format="%Y/%m/%d", errors="coerce").min()
    if pd.isna(d):
        raise RuntimeError("no valid dates in column {}".format(column))
    for i in range(len(df)):
        cur = df.loc[i, column]
        if pd.isna(cur):
            df.loc[i, column] = d
            continue
        try:
            d = canon_date(cur)
        except ValueError:
            pass
        df.loc[i, column] = d


def from_csv(csv_file):
    print("Reading {}".format(csv_file))
    df = pd.read_csv(csv_file)
    return df


def rbc_chequing(dfs: list[DataFrame], base_dir: str = "."):
    # print ("Processing chequing account in {}".format(base_dir))
    # csv_files = glob.glob(f"{base_dir}/**/*.csv", recursive=True)
    # dfs = [from_csv(f) for f in csv_files]

    # drop any dataframe that includes the column "Transaction Date"
    dfs = [df for df in dfs if "Transaction Date" not in df.columns]
    if len(dfs) == 0:
        return

    df = pd.concat(dfs, ignore_index=True)  # if there are any rows, save the csv

    if len(df) == 0:
        return

    clean_date_column(df, "Date")
    df["Withdrawals"] = df["Withdrawals"].astype(float)
    df["Deposit"] = df["Deposit"].astype(float)
    df.fillna(value={"Withdrawals": 0.0, "Deposit": 0.0}, inplace=True)
    df["Description"] = df["Description"].apply(lambda d: d.replace("\n", " "))

    df["Amount"] = (df["Withdrawals"] * -1.0) + df["Deposit"]
    df.drop(columns=["Withdrawals", "Deposit"], inplace=True)
    df = df[["Date", "Description", "Amount", "Balance"]]
    df.sort_values(by=["Date"], ascending=True, kind="mergesort", inplace=True)

    # filter out rows that include "Opening or Closing Balance" in the description
    df = df[~df["Description"].str.contains("opening balance", na=False, case=False)]
    df = df[~df["Description"].str.contains("Closing balance", na=False, case=False)]

    if len(df) == 0:
        return

    # remove trailing slashes in the base_dir filename and replace leading "." with empty string
    output_filename = f"{base_dir.rstrip("/")}_account.csv"
    df.to_csv(output_filename, index=False)


def rbc_mastercard(dfs: list[DataFrame], base_dir: str = "."):
    # Read all CSV files in the directory and subdirectories
    # and concatenate them into a single dataframe

    # update the glob pattern to include all subdirectories from the base_dir

    # cc_csv_files = glob.glob(f"{base_dir}/**/*.csv", recursive=True)
    # dfs = [from_csv(f) for f in cc_csv_files]

    # drop any dataframe that don't include the column "Transaction Date"
    dfs = [df for df in dfs if "Transaction Date" in df.columns]
    if len(dfs) == 0:
        return

    df = pd.concat(dfs, ignore_index=True)

    if len(df) == 0:
        return

    clean_date_column(df, "Transaction Date")
    clean_date_column(df, "Posting Date")
    df["Amount"] = df["Amount"].astype(float)

    # Make purchases on credit card negative, credits positive.
    df["Amount"] = df["Amount"] * -1
    # Filter out automatic payment to pay off credit card balance.
    if "Activity Description" in df.columns:
        df.rename(columns={"Activity Description": "Description"}, inplace=True)
    df["Description"] = df["Description"].apply(lambda d: d.replace("\n", " "))
    # filter out rows that include "PAYMENT - THANK YOU" in the description
    # df = df[~df["Description"].str.contains("PAYMENT - THANK YOU", na=False)]
    # if len(df) == 0:
    #   return
    df.sort_values(
        by=["Transaction Date"], ascending=True, kind="mergesort", inplace=True
    )
    df.to_csv(f"{base_dir.rstrip("/")}_cc.csv", index=False)


def main(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "csv_files",
        default=glob.glob("**/*.csv", recursive=True),
        nargs="*",
        help="input PDF statements (default: **/*.csv)",
    )

    args = parser.parse_args()
    csv_files = [f for f in args.csv_files if os.path.isfile(f)]
    csv_files += [
        f
        for d in args.csv_files
        if os.path.isdir(d)
        for f in glob.glob(d + "/**/*.csv", recursive=True)
    ]

    if len(csv_files) == 0:
        print("No PDF files found.")
        return 1

    csv_files.sort()

    # iterate through all the csv files and resolve the nearest common parent directory
    base_dir = os.path.dirname(csv_files[0])
    for f in csv_files:
        while not os.path.commonpath([base_dir, f]) == base_dir:
            base_dir = os.path.dirname(base_dir)
            if base_dir == "." or base_dir == "/" or base_dir == "":
                break

    dfs = [from_csv(f) for f in csv_files]

    rbc_chequing(dfs, base_dir=base_dir)
    rbc_mastercard(dfs, base_dir=base_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
