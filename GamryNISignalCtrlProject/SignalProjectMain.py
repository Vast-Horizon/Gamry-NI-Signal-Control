import GamrySignalImport
import NIProjectImport

def main():
    num = int(input("num: "))
    if num==1:
        GamrySignalImport.mainfunc()
    elif num==2:
        NIProjectImport.mainfunc()

if __name__ == "__main__":
    main()