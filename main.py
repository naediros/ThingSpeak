import database

def test():
    import pandas as pd

    db = database.Database(verbose=True)
    df = db.get_all_data()

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df.describe())

test()