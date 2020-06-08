import pytest
from rnalysis.utils import *


def test_is_df_dataframe():
    my_df = pd.DataFrame()
    assert (check_is_df_like(my_df))


def test_is_df_str():
    correct_path = "myfile.csv"
    correct_path_2 = r"myfolder\anotherfile.csv"
    assert (not check_is_df_like(correct_path))
    assert (not check_is_df_like(correct_path_2))


def test_is_df_pathobj():
    correct_pathobj = Path("all_feature_96_new.csv")
    assert (not check_is_df_like(correct_pathobj))


def test_is_df_str_notcsv():
    incorrect_pth = "myfile.xlsx"
    incorrect_pth2 = "all_feature_96_new"
    with pytest.raises(ValueError):
        check_is_df_like(incorrect_pth)
    with pytest.raises(ValueError):
        check_is_df_like(incorrect_pth2)


def test_is_df_pathobj_notcsv():
    incorrect_pathobj = Path("test_general.py")
    with pytest.raises(ValueError):
        check_is_df_like(incorrect_pathobj)


def test_is_df_invalid_type():
    invalid_type = 67
    with pytest.raises(ValueError):
        check_is_df_like(invalid_type)


def test_remove_unindexed_rows():
    truth = load_csv("test_files/counted_missing_rows_deleted.csv", 0)
    missing = load_csv("test_files/counted_missing_rows.csv", 0)
    assert (truth == remove_unindexed_rows(missing)).all().all()


def test_load_csv_bad_input():
    invalid_input = 2349
    with pytest.raises(AssertionError):
        a = load_csv(invalid_input)


def test_load_csv():
    truth = pd.DataFrame({'idxcol': ['one', 'two', 'three'], 'othercol': [4, 5, 6]})
    truth.set_index('idxcol', inplace=True)
    pth = "test_files/test_load_csv.csv"
    assert (truth == load_csv(pth, 0)).all().all()


def test_biotype_table_assertions():
    assert False


def test_attr_table_assertions():
    assert False


def test_get_settings_file():
    make_temp_copy_of_test_file()
    set_temp_copy_of_test_file_as_default()
    assert False


def test_get_attr_ref_path():
    make_temp_copy_of_test_file()
    set_temp_copy_of_test_file_as_default()
    assert False


def test_get_biotype_ref_path():
    make_temp_copy_of_test_file()
    set_temp_copy_of_test_file_as_default()
    assert False


def test_save_csv():
    assert False