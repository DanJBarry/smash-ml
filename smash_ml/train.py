from pandas import DataFrame, concat
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import GaussianNB

_gnb = GaussianNB()
_gnb_correct = 0
_gnb_total = 0

_sgdc = SGDClassifier()
_sgdc_correct = 0
_sgdc_total = 0


def train_gnb(train_sets, train_upset, test_sets, test_upset):
    global _gnb, _gnb_correct, _gnb_total
    _gnb = _gnb.partial_fit(train_sets, train_upset, [0, 1])
    predictions = _gnb.predict(test_sets)
    zipped_predictions = list(zip(test_upset, predictions))
    run_correct = (test_upset.to_numpy() == predictions).sum()
    upsets_correct = 0
    upsets_missed = 0
    upsets_incorrect = 0
    non_upsets_correct = 0
    for real, predicted in zipped_predictions:
        if real == 1 and predicted == 1:
            upsets_correct += 1
        if real == 1 and predicted == 0:
            upsets_missed += 1
        if real == 0 and predicted == 1:
            upsets_incorrect += 1
        if real == 0 and predicted == 0:
            non_upsets_correct += 1
    run_correct = upsets_correct + non_upsets_correct
    run_total = len(predictions)
    _gnb_correct += run_correct
    _gnb_total += run_total
    print("Gaussian Naive Bayes results:")
    print(f"Overall accuracy: {round(_gnb_correct / _gnb_total, 3)}")
    print(f"Tournament accuracy: {round(run_correct / run_total, 3)}")
    print(f"Upsets correctly predicted: {upsets_correct}")
    print(f"Upsets incorrectly predicted: {upsets_incorrect}")
    print(f"Upsets missed: {upsets_missed}\n")


def train_sgdc(train_sets, train_upset, test_sets, test_upset):
    global _sgdc, _sgdc_correct, _sgdc_total
    _sgdc = _sgdc.partial_fit(train_sets, train_upset, [0, 1])
    predictions = _sgdc.predict(test_sets)
    zipped_predictions = list(zip(test_upset, predictions))
    upsets_correct = 0
    upsets_missed = 0
    upsets_incorrect = 0
    non_upsets_correct = 0
    for real, predicted in zipped_predictions:
        if real == 1 and predicted == 1:
            upsets_correct += 1
        if real == 1 and predicted == 0:
            upsets_missed += 1
        if real == 0 and predicted == 1:
            upsets_incorrect += 1
        if real == 0 and predicted == 0:
            non_upsets_correct += 1
    run_correct = upsets_correct + non_upsets_correct
    run_total = len(predictions)
    _sgdc_correct += run_correct
    _sgdc_total += run_total
    print("Linear SVM results:")
    print(f"Overall accuracy: {round(_sgdc_correct / _sgdc_total, 3)}")
    print(f"Tournament accuracy: {round(run_correct / run_total, 3)}")
    print(f"Upsets correctly predicted: {upsets_correct}")
    print(f"Upsets incorrectly predicted: {upsets_incorrect}")
    print(f"Upsets missed: {upsets_missed}\n")


def train(sets: DataFrame):
    print(f"Processing {len(sets)} sets\n")
    sets = sets.drop_duplicates()
    train_sets = sets.sample(frac=0.8)
    test_sets = concat([sets, train_sets]).drop_duplicates(keep=False)
    train_upset = train_sets.pop("upset").astype("int")
    test_upset = test_sets.pop("upset").astype("int")
    train_gnb(train_sets, train_upset, test_sets, test_upset)
    train_sgdc(train_sets, train_upset, test_sets, test_upset)
