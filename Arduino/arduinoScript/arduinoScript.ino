#include <HX711_ADC.h>
#include <EEPROM.h>

const int CAL_BUTT = 11;
unsigned long lastPollTime = 0;
const int printInterval = 100;

// constants for shelf 1
const int LC1_DOUT = 2; 
const int LC1_SCK = 3;
const int BLUE_LED = 8;
const int eeprom_a1 = 0;
HX711_ADC LoadCell_1(LC1_DOUT, LC1_SCK);

// constants for shelf 2
const int LC2_DOUT = 6; 
const int LC2_SCK = 7;
const int GREEN_LED = 9;
const int eeprom_a2 = 50;
HX711_ADC LoadCell_2(LC2_DOUT, LC2_SCK);

// constants for shelf 3
const int LC3_DOUT = 4; 
const int LC3_SCK = 5;
const int WHITE_LED = 10;
const int eeprom_a3 = 100;
HX711_ADC LoadCell_3(LC3_DOUT, LC3_SCK);

// start each LC use eeprom calVals 
void setup() {
  EEPROM.begin();
  Serial.println("\nStarting"); 
  Serial.begin(57600); delay(10);
  pinMode(CAL_BUTT, INPUT);

  // setup will zero out each LC
  setupLC(LoadCell_1, BLUE_LED, eeprom_a1);
  setupLC(LoadCell_2, GREEN_LED, eeprom_a2);
  setupLC(LoadCell_3, WHITE_LED, eeprom_a3);

  Serial.println("Setup Done");
}

// (blocking) setup method for a LC 
void setupLC(HX711_ADC& LoadCell, int LED_PIN, int eeprom_loc) {
  float cv= 0.0f;
  int stabilizingTime = 2000;
  pinMode(LED_PIN, OUTPUT);
  LoadCell.begin();
  LoadCell.start(stabilizingTime, true);
  EEPROM.get(eeprom_loc, cv);
  if (isnan(cv)){ 
    Serial.println("Failed to read eeprom");
    cv = 1.0;}
  LoadCell.setCalFactor(cv);
  while (!LoadCell.update());
  Serial.print("Started LC with calVal=");
  Serial.println(cv);
  digitalWrite(LED_PIN, HIGH);
}

// (blocking) flash an led until button pressed 
void waitForDebugButton(int LED_PIN, int interval){
  unsigned long t = 0;
  int ledState = 0;
  while ( digitalRead(CAL_BUTT) != HIGH ){
    if (millis() - t >= interval){
      digitalWrite(LED_PIN, ledState);
      t = millis();
      ledState = 1 - ledState;}}
  digitalWrite(LED_PIN, HIGH);
}

// (blocking) run calibration on a given LC
void calibrateLC(HX711_ADC& LoadCell, int LED_PIN, int eeprom_loc) {
  Serial.println("Running Calibration for LC");

  // zero out the LC
  Serial.println("Remove all mass from the LC");
  waitForDebugButton(LED_PIN, 250);  
  LoadCell.update();
  LoadCell.tare();

  // get known mass
  Serial.println("Add known mass to the LC");
  waitForDebugButton(LED_PIN, 150); 
  LoadCell.update();
  LoadCell.refreshDataSet();

  // get and save new calFactor 
  float calVal = LoadCell.getNewCalibration(1000.0);
  Serial.print("Got new calVal of ");
  Serial.println(LoadCell.getCalFactor());
  EEPROM.put(eeprom_loc, calVal);
}

void loop() {

  // pull data from the LCs, output to serial 
  LoadCell_1.update();
  LoadCell_2.update();
  LoadCell_3.update();
  if ( millis() - lastPollTime > printInterval ){
    Serial.print(String(millis(), 4) + " ");
    Serial.print(String(LoadCell_1.getData()) + " ");
    Serial.print(String(LoadCell_2.getData()) + " ");
    Serial.println(String(LoadCell_3.getData()));
    lastPollTime = millis();}

  // calibration commands
  if (Serial.available() > 0){
    int x = Serial.parseInt();
    if (x == 1){
      calibrateLC(LoadCell_1, BLUE_LED, eeprom_a1);}
    if (x == 2){
      calibrateLC(LoadCell_2, GREEN_LED, eeprom_a2);}
    if (x == 3){
      calibrateLC(LoadCell_3, WHITE_LED, eeprom_a3);}}  
}