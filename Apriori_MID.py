#!/usr/bin/env python
# coding: utf-8

import argparse
import itertools
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder

# Parse the CLI Arguments
parser = argparse.ArgumentParser()

parser.add_argument("-db", "--database", dest = "db", default = "Amazon", help="Database name")
parser.add_argument("-s", "--support",dest = "min_supp", help="Min Support", type=float , required=True)
parser.add_argument("-c", "--confidence",dest = "min_conf", help="Min Confidence", type=float , required=True)

args = parser.parse_args()

print("\nDB selected: {}, Min Support: {}, Min Confidence: {}\n".format(args.db, args.min_supp, args.min_conf))

# Read the dataset
dataset = pd.ExcelFile("Data/{}.xlsx".format(args.db))
dataset

# Convert the sheets to DataFrame
sheet_to_df_map = {}
list_of_sheets = dataset.sheet_names
for sheet_name in list_of_sheets:
    indx = "Item #" if "Item" in sheet_name else "Transaction ID"    
    cols = dataset.parse(sheet_name).columns
    sheet_to_df_map[sheet_name] = dataset.parse(sheet_name)    
    if indx == "Transaction ID":
        sheet_to_df_map[sheet_name]['Transaction'] = sheet_to_df_map[sheet_name]['Transaction'].apply(lambda x: sorted([y.strip(' ') for y in x.split(",") if y.strip(' ') != '']))        
    else:
        sheet_to_df_map[sheet_name]['Item'] = sheet_to_df_map[sheet_name]['Item'].apply(lambda x: x.strip(' '))            

# Get the list of items from Item column
items = list(sheet_to_df_map['Item'].Item)

# Get the transactions from Transaction column
trans = sheet_to_df_map['Transaction']


trans_list = list(trans.Transaction)
trans_list


te = TransactionEncoder()
te_data = te.fit(list(trans["Transaction"])).transform(list(trans["Transaction"]))
df1 = pd.DataFrame(te_data.astype("int"), columns=te.columns_)
frequent_item = df1.transpose()


min_supp = args.min_supp

supp = pd.DataFrame(df1.sum()/len(frequent_item.columns), columns=["Support"])
newlst = sorted(list(supp[supp["Support"]  >= min_supp ].index))


def make_combos(lst, key1 = 0):
    combinations = {}
    for L in range(1, len(lst)+1):
        if L != key1:
            combo = []
            for subset in itertools.combinations(lst, L):
                combo.append(list(subset))
            combinations[L] = combo
    return combinations

combinations = make_combos(newlst)


new_combo = {}
idx = 0
for key, val in combinations.items():
    count = 0
    new_lst = []
    for lst in val:
        idx += 1
        bools = [ 1 if (set(lst).issubset(set(elem))) else 0 for elem in trans_list ]        
        if not 1 in bools:            
            val.remove(lst)
        else:
            count = bools.count(1)       
            new_lst.append([lst,count/len(frequent_item.columns)])
        new_combo[idx] = [sorted(lst), count/len(frequent_item.columns)]    

final = pd.DataFrame(new_combo.values(),columns=["Items","Support"])


new_final = final[final["Support"] >= min_supp].reset_index(drop=True)


highst_len = 0
if new_final.shape[0] != 0:
    highst_len = len(new_final.Items.iloc[-1])
final_comb = new_final[new_final['Items'].str.len() == highst_len].reset_index(drop=True)


cols = ["Item1","Item2","Support1","Support2","Confidence"]
conf_df = pd.DataFrame(columns=cols)
for item_lst in final_comb.Items:
    supp_item = new_final[new_final['Items'].apply(lambda x: x == item_lst)].values[0][1]
    assc_combo = make_combos(item_lst,highst_len)
    for key, val in assc_combo.items():
        for item in val:            
            item2 = sorted(list(set(item_lst) - set(item)))
            item_set = new_final[new_final['Items'].apply(lambda x: x == item2)]
            if item_set.shape[0] != 0:
                supp_item2 = item_set.values[0][1]
                if supp_item2 > 0:
                    confidence = supp_item / supp_item2    
                    if confidence >= args.min_conf:
                        print("{x} -> {y}".format(x=item, y= item2))
                        print("Confidence = Supp({x}) / Supp{y}".format(x=item_lst, y= item2))
                        print("           = {x} / {y}".format(x=supp_item, y=supp_item2))
                        print("           = {x:.2f}\n".format(x=confidence))
                    dict_lst = [item,item2,supp_item,supp_item2,confidence]
                    res = {cols[i]: dict_lst[i] for i in range(len(cols))}
                    conf_df = conf_df.append(res, ignore_index=True)


conf_matrix = conf_df[conf_df["Confidence"] >= args.min_conf].reset_index(drop=True)
