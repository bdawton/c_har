
    #include "myinlinetree.h"
    #include <eml_test.h>

    static void classify(const float *values, int length, int row) {
        const int32_t class = myinlinetree_predict(values, length);
        printf("%d,%d\n", row, class);
    }
    int main() {
        eml_test_read_csv(stdin, classify);
    }
    