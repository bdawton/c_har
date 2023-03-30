#include <SPI.h>
#include <SD.h>
#define chipSelect BUILTIN_SDCARD
#include "quickSort.h"
#include <limits.h>
#include "classifier_to_test_1650.h"
#define DATA_LEN 50
#define X_FEATURE_LEN 5
#define Y_FEATURE_LEN 5
#define Z_FEATURE_LEN 5
#define FEATURE_LEN 15

File x_dataFile;
File y_dataFile;
File z_dataFile;
File labelFile;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect.
  }
  Serial.print("Initializing SD card...");
  if (!SD.begin(chipSelect)) {
    Serial.println("initialization failed!");
    return;
  }
  Serial.println("initialization done.");
}

void loop() {

  labelFile = SD.open("lab_1650.txt");
  x_dataFile = SD.open("x_c_mea_1650.txt");
  y_dataFile = SD.open("y_c_mea_1650.txt");
  z_dataFile = SD.open("z_c_mea_1650.txt");

  int l_index = 0;
  int labels[DATA_LEN];

  while (labelFile.available())
  {
    char lChar = labelFile.read();     
        if(lChar != '\n')
        {     
 //         Serial.println(lChar-'0');       
    labels[l_index] = lChar-'0'; // single char to int conversion
    l_index++;
        }
  }

//   for (int rr = 0; rr < l_index; ++rr) {
//    Serial.println(labels[rr]); }

//----------------------------------l------------------------


    int p_index = 0;
    int pred_labels[l_index];
    float ex_features[FEATURE_LEN];

    while (z_dataFile.available()) //the last one
    {

    char x_datafileContents[24]; // Probably can be smaller
    float x_data[DATA_LEN];
    float x_ex_features[X_FEATURE_LEN];
    float x_Mtemp = 0;
    float x_mean = 0;
    float x_var = 0;
    float x_std = 0;
    float x_median = 0;
    float x_first_q = 0;
    float x_third_q = 0;
    float x_iqr = 0;
    float x_maxv = 0;
    float x_minv = 0;
    float x_abslargest = 0;
    int x_left = 0;
    int x_right = DATA_LEN - 1;
    byte x_index = 0;
    int x_data_index = 0;

    long int tic_feature_extraction = micros();



      
      while (x_data_index < DATA_LEN) {

        char x_dChar = x_dataFile.read();
        x_datafileContents[x_index++] = x_dChar;
        //   datafileContents[index] = '\0'; // NULL terminate the array DO I NEED THIS LINE?

        if ((x_dChar == '\n') || (x_dChar == ','))
        {
          if (strlen(x_datafileContents) > 0)
          {
            x_data[x_data_index] = atof(x_datafileContents);
            //      Serial.println(data[data_index], 12);
            x_data_index++;
          }
          x_datafileContents[0] = '\0';
          x_index = 0;
        }
      }


   
      quickSort(x_data, x_left, x_right);

      //  for (int tt = 0; tt < DATA_LEN; ++tt)
      //  {Serial.println(data[tt]);
      //  }

      for ( int x_l = 0; x_l < DATA_LEN; ++x_l) {
        float x_delta = x_data[x_l] - x_mean;
        x_mean += x_delta / (x_l + 1);
        x_Mtemp += x_delta * (x_data[x_l] - x_mean);
        x_var = x_Mtemp / (x_l + 1);
      }


      Serial.print("Entry number x: ");
      Serial.println(p_index);

      x_std = sqrt(x_var);
      Serial.print("The x mean value is: ");
      Serial.println(x_mean);
      Serial.print("The x standard deviation is: ");
      Serial.println(x_std);

      if (DATA_LEN % 2) {
        int x_m = DATA_LEN / 2;
        x_median = x_data[x_m];

        if (x_m % 2) {
          x_first_q = (x_data[x_m / 2 ] + x_data[x_m / 2 + 1]) / 2;
          x_third_q = (x_data[DATA_LEN - (x_m / 2) - 2] + x_data[DATA_LEN - (x_m / 2) - 1]) / 2;
//          Serial.println("waawaaweewaa");
        }
        else {
          x_first_q = (x_data[x_m / 2]);
          x_third_q = x_data[DATA_LEN - (x_m / 2 + 1)];
//          Serial.println("kinginthecastle");
        }
      }
      else {
        int x_leftm = DATA_LEN / 2 - 1;
        int x_rightm = DATA_LEN / 2;
        x_median = (x_data[x_leftm] + x_data[x_rightm]) / 2;
        if (x_leftm % 2 == 0 ) {
          x_first_q = (x_data[x_leftm / 2]);
          x_third_q = x_data[DATA_LEN - (x_rightm / 2) - 1];
//          Serial.println("gypsytears");
        }
        else {
          x_first_q = (x_data[x_leftm / 2 ] + x_data[x_leftm / 2 + 1]) / 2;
          x_third_q = (x_data[DATA_LEN - (x_rightm / 2)] + x_data[DATA_LEN - (x_rightm / 2) - 1]) / 2;
//          Serial.println("uktarthehawk");

        }
      }

      x_iqr = (x_third_q - x_first_q);
      Serial.print("The x median value is: ");
      Serial.println(x_median);
      Serial.print("The x first quartile value is: ");
      Serial.println(x_first_q);
      Serial.print("The x third quartile value is: ");
      Serial.println(x_third_q);
      Serial.print("The x inter-quartile range value is: ");
      Serial.println(x_iqr);

      x_minv = x_data[x_left];
      x_maxv = x_data[x_right];
      if (abs(x_maxv) >= abs(x_minv))
      {
        x_abslargest = x_maxv;
      }
      else {
        x_abslargest = abs(x_minv);
      }
      
      Serial.print("The x min value is: ");
      Serial.println(x_minv);
      Serial.print("The x max value is: ");
      Serial.println(x_maxv);
      Serial.print("The x abslargest value is: ");
      Serial.println(x_abslargest);

     

      x_ex_features[0] = x_mean;
      x_ex_features[1] = x_std;
      x_ex_features[2] = x_median;
      x_ex_features[3] = x_abslargest;
      x_ex_features[4] = x_iqr;

      ex_features[0] = x_mean;
      ex_features[1] = x_std;
      ex_features[2] = x_median;
      ex_features[3] = x_abslargest;
      ex_features[4] = x_iqr;



    char y_datafileContents[24]; // Probably can be smaller
    float y_data[DATA_LEN];
    float y_ex_features[Y_FEATURE_LEN];
    float y_Mtemp = 0;
    float y_mean = 0;
    float y_var = 0;
    float y_std = 0;
    float y_median = 0;
    float y_first_q = 0;
    float y_third_q = 0;
    float y_iqr = 0;
    float y_maxv = 0;
    float y_minv = 0;
    float y_abslargest = 0;
    int y_left = 0;
    int y_right = DATA_LEN - 1;
    byte y_index = 0;
    int y_data_index = 0;


      
      while (y_data_index < DATA_LEN) {

        char y_dChar = y_dataFile.read();
        y_datafileContents[y_index++] = y_dChar;
        //   datafileContents[index] = '\0'; // NULL terminate the array DO I NEED THIS LINE?

        if ((y_dChar == '\n') || (y_dChar == ','))
        {
          if (strlen(y_datafileContents) > 0)
          {
            y_data[y_data_index] = atof(y_datafileContents);
            //      Serial.println(data[data_index], 12);
            y_data_index++;
          }
          y_datafileContents[0] = '\0';
          y_index = 0;
        }
      }
   
      quickSort(y_data, y_left, y_right);

      //  for (int tt = 0; tt < DATA_LEN; ++tt)
      //  {Serial.println(data[tt]);
      //  }

      for ( int y_l = 0; y_l < DATA_LEN; ++y_l) {
        float y_delta = y_data[y_l] - y_mean;
        y_mean += y_delta / (y_l + 1);
        y_Mtemp += y_delta * (y_data[y_l] - y_mean);
        y_var = y_Mtemp / (y_l + 1);
      }


      Serial.print("Entry number y: ");
      Serial.println(p_index);

      y_std = sqrt(y_var);
      Serial.print("The y mean value is: ");
      Serial.println(y_mean);
      Serial.print("The y standard deviation is: ");
      Serial.println(y_std);

      if (DATA_LEN % 2) {
        int y_m = DATA_LEN / 2;
        y_median = y_data[y_m];

        if (y_m % 2) {
          y_first_q = (y_data[y_m / 2 ] + y_data[y_m / 2 + 1]) / 2;
          y_third_q = (y_data[DATA_LEN - (y_m / 2) - 2] + y_data[DATA_LEN - (y_m / 2) - 1]) / 2;
//          Serial.println("waawaaweewaa");
        }
        else {
          y_first_q = (y_data[y_m / 2]);
          y_third_q = y_data[DATA_LEN - (y_m / 2 + 1)];
//          Serial.println("kinginthecastle");
        }
      }
      else {
        int y_leftm = DATA_LEN / 2 - 1;
        int y_rightm = DATA_LEN / 2;
        y_median = (y_data[y_leftm] + y_data[y_rightm]) / 2;
        if (y_leftm % 2 == 0 ) {
          y_first_q = (y_data[y_leftm / 2]);
          y_third_q = y_data[DATA_LEN - (y_rightm / 2) - 1];
//          Serial.println("gypsytears");
        }
        else {
          y_first_q = (y_data[y_leftm / 2 ] + y_data[y_leftm / 2 + 1]) / 2;
          y_third_q = (y_data[DATA_LEN - (y_rightm / 2)] + y_data[DATA_LEN - (y_rightm / 2) - 1]) / 2;
//          Serial.println("uktarthehawk");

        }
      }

      y_iqr = (y_third_q - y_first_q);
      Serial.print("The y median value is: ");
      Serial.println(y_median);
      Serial.print("The y first quartile value is: ");
      Serial.println(y_first_q);
      Serial.print("The y third quartile value is: ");
      Serial.println(y_third_q);
      Serial.print("The y inter-quartile range value is: ");
      Serial.println(y_iqr);

      y_minv = y_data[y_left];
      y_maxv = y_data[y_right];
      if (abs(y_maxv) >= abs(y_minv))
      {
        y_abslargest = y_maxv;
      }
      else {
        y_abslargest = abs(y_minv);
      }

      Serial.print("The y min value is: ");
      Serial.println(y_minv);
      Serial.print("The y max value is: ");
      Serial.println(y_maxv);
      Serial.print("The y abslargest value is: ");
      Serial.println(y_abslargest);

      y_ex_features[0] = y_mean;
      y_ex_features[1] = y_std;
      y_ex_features[2] = y_median;
      y_ex_features[3] = y_abslargest;
      y_ex_features[4] = y_iqr;

      ex_features[5] = y_mean;
      ex_features[6] = y_std;
      ex_features[7] = y_median;
      ex_features[8] = y_abslargest;
      ex_features[9] = y_iqr;


    char z_datafileContents[24]; // Probably can be smaller
    float z_data[DATA_LEN];
    float z_ex_features[Z_FEATURE_LEN];
    float z_Mtemp = 0;
    float z_mean = 0;
    float z_var = 0;
    float z_std = 0;
    float z_median = 0;
    float z_first_q = 0;
    float z_third_q = 0;
    float z_iqr = 0;
    float z_maxv = 0;
    float z_minv = 0;
    float z_abslargest = 0;
    int z_left = 0;
    int z_right = DATA_LEN - 1;
    byte z_index = 0;
    int z_data_index = 0;


      
      while (z_data_index < DATA_LEN) {

        char z_dChar = z_dataFile.read();
        z_datafileContents[z_index++] = z_dChar;
        //   datafileContents[index] = '\0'; // NULL terminate the array DO I NEED THIS LINE?

        if ((z_dChar == '\n') || (z_dChar == ','))
        {
          if (strlen(z_datafileContents) > 0)
          {
            z_data[z_data_index] = atof(z_datafileContents);
            //      Serial.println(data[data_index], 12);
            z_data_index++;
          }
          z_datafileContents[0] = '\0';
          z_index = 0;
        }
      }
   
      quickSort(z_data, z_left, z_right);

      //  for (int tt = 0; tt < DATA_LEN; ++tt)
      //  {Serial.println(data[tt]);
      //  }

      for ( int z_l = 0; z_l < DATA_LEN; ++z_l) {
        float z_delta = z_data[z_l] - z_mean;
        z_mean += z_delta / (z_l + 1);
        z_Mtemp += z_delta * (z_data[z_l] - z_mean);
        z_var = z_Mtemp / (z_l + 1);
      }


      Serial.print("Entry number y: ");
      Serial.println(p_index);

      z_std = sqrt(z_var);
      Serial.print("The z mean value is: ");
      Serial.println(z_mean);
      Serial.print("The z standard deviation is: ");
      Serial.println(z_std);

      if (DATA_LEN % 2) {
        int z_m = DATA_LEN / 2;
        z_median = z_data[z_m];

        if (z_m % 2) {
          z_first_q = (z_data[z_m / 2 ] + z_data[z_m / 2 + 1]) / 2;
          z_third_q = (z_data[DATA_LEN - (z_m / 2) - 2] + z_data[DATA_LEN - (z_m / 2) - 1]) / 2;
//          Serial.println("waawaaweewaa");
        }
        else {
          z_first_q = (z_data[z_m / 2]);
          z_third_q = z_data[DATA_LEN - (z_m / 2 + 1)];
//          Serial.println("kinginthecastle");
        }
      }
      else {
        int z_leftm = DATA_LEN / 2 - 1;
        int z_rightm = DATA_LEN / 2;
        z_median = (z_data[z_leftm] + z_data[z_rightm]) / 2;
        if (z_leftm % 2 == 0 ) {
          z_first_q = (z_data[z_leftm / 2]);
          z_third_q = z_data[DATA_LEN - (z_rightm / 2) - 1];
//          Serial.println("gypsytears");
        }
        else {
          z_first_q = (z_data[z_leftm / 2 ] + z_data[z_leftm / 2 + 1]) / 2;
          z_third_q = (z_data[DATA_LEN - (z_rightm / 2)] + z_data[DATA_LEN - (z_rightm / 2) - 1]) / 2;
//          Serial.println("uktarthehawk");

        }
      }

      z_iqr = (z_third_q - z_first_q);
      Serial.print("The z median value is: ");
      Serial.println(z_median);
      Serial.print("The z first quartile value is: ");
      Serial.println(z_first_q);
      Serial.print("The z third quartile value is: ");
      Serial.println(z_third_q);
      Serial.print("The z inter-quartile range value is: ");
      Serial.println(z_iqr);

      z_minv = z_data[z_left];
      z_maxv = z_data[z_right];
      if (abs(z_maxv) >= abs(z_minv))
      {
        z_abslargest = z_maxv;
      }
      else {
        z_abslargest = abs(z_minv);
      }

      Serial.print("The z min value is: ");
      Serial.println(z_minv);
      Serial.print("The z max value is: ");
      Serial.println(z_maxv);
      Serial.print("The z abslargest value is: ");
      Serial.println(z_abslargest);

      z_ex_features[0] = z_mean;
      z_ex_features[1] = z_std;
      z_ex_features[2] = z_median;
      z_ex_features[3] = z_abslargest;
      z_ex_features[4] = z_iqr;

      ex_features[10] = z_mean;
      ex_features[11] = z_std;
      ex_features[12] = z_median;
      ex_features[13] = z_abslargest;
      ex_features[14] = z_iqr;

      long int toc_feature_extraction = micros();
      Serial.print("Time taken by feature extraction: "); 
      Serial.print(toc_feature_extraction-tic_feature_extraction); 
      Serial.println(" microseconds");

      long int tic_classification = micros();
      int pred_label = classifier_to_test_1650_predict(ex_features, FEATURE_LEN);
      pred_labels[p_index] = pred_label;
      long int toc_classification = micros();
      
      Serial.print("Real Label: ");
      Serial.println(labels[p_index]);
      Serial.print("Predicted Label: ");
      Serial.println(pred_label);
      ++p_index;
      Serial.println("---------------------");
      Serial.print("Time taken by classification: "); 
      Serial.print(toc_classification-tic_classification); 
      Serial.println(" microseconds");
      delay(200);
      Serial.println("---------------------");
      
 } //This is the original end of the file.available while loop




 Serial.println("---------------------");
int correct = 0;
for (int acc = 0; acc <p_index; ++acc){
   if (labels[acc] == pred_labels[acc]) {
      ++correct;
    }
}

  Serial.println(correct);
  Serial.println(p_index);

  float accuracy = (float(correct) / float(p_index));

  Serial.print("Accuracy: ");
  Serial.println(accuracy, 3);
  delay(10000);
 Serial.println("---------------------");

 }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
 
