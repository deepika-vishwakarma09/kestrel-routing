"""One command: clean, train, check, predict, cost it. Then start the service yourself (see README)."""
from src import business, clean, evaluate, predict, train


def main():
    print("1/5 cleaning...");    clean.run()
    print("2/5 training...");    train.run()
    print("3/5 evaluating (backtests)...");  evaluate.run()
    print("4/5 predicting...");  predict.run()
    print("5/5 costing...");     business.run()


if __name__ == "__main__":
    main()
