# RBC PDF to CSV converter using Gemini

This is a simple PDF to CSV converter for Visa and Account statements. It uses a single shot prompt to Gemini to perform
the conversion. There are two commands available:

## `pdf2csv.py` - Convert the DPF to CSV

You can pass any file or directory as parameters. The tool will detect (naively) if it is a Credit Card statement or a
Bank Statement. The difference is which columns are produced and how some of the coersion works.

For Bank statements, the following columns are included:

* Date
* Description
* Withdrawl
* Deposit
* Balance

For Credit Card statements, the following columns are included:

* Transaction Date
* Posted Date
* Description
* Amount

For CC statements, details such as Fx conversion is included in the Description.

## `merge_csv.py` - merge a directory of CSV files into a common list of files

This will produce up to two files suffixed with either `_account.csv` for the aggregation of all the bank statements and `_cc.csv` for the aggregation of all the Credit Card Statemnts.

The utility of this is that it ensures date fields are correct and merges debits/credits into a single amount column. It also removes the opening and closing balances.
