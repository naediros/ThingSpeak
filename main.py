import database

def test():


    db = database.Database(verbose=True)
    db.create_src_data_tables()
    db.retrieve_latest_entries_from_ts()


test()