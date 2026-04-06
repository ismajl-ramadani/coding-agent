from functions.get_files_info import get_files_info


def test_get_files_info():
    result = get_files_info(working_directory="calculator", directory=".")
    print("Result for current directory:")
    print(result)
    print("\n")

    result = get_files_info(working_directory="calculator", directory="pkg")
    print("Result for 'pkg' directory:")
    print(result)
    print("\n")

    result = get_files_info(working_directory="calculator", directory="/bin")
    print("Result for '/bin' directory:")
    print(result)
    print("\n")

    result = get_files_info(working_directory="calculator", directory="../")
    print("Result for '/bin' directory:")
    print(result)
    print("\n")
    
if __name__ == "__main__":
    test_get_files_info()