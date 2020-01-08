from sys import argv

class validate():
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def read_csv(self):
        return(self.csv_file)

def main():
    csv_file = argv[1]
    validation = validate(csv_file)
    validation.read_csv()

if __name__ == '__main__':
    main()
