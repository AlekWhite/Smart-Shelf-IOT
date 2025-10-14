#include <HX711_ADC.h>
#include <EEPROM.h>

const int CAL_BUTT = 11;
unsigned long lastPollTime = 0;
const int printInterval = 10;

// constants for shelf 1
const int LC1_DOUT = 2; 
const int LC1_SCK = 3;
const int BLUE_LED = 8;
const int eeprom_a1 = 0;
HX711_ADC LoadCell_1(LC1_DOUT, LC1_SCK);

// start each LC use eeprom calVals 
void setup() {
  EEPROM.begin();
  float cv= 0.0f;
  int stabilizingTime = 2000;
  Serial.println("\nStarting"); 
  Serial.begin(57600); delay(10);
  pinMode(CAL_BUTT, INPUT);
  
  // start LC1
  pinMode(BLUE_LED, OUTPUT);
  LoadCell_1.begin();
  LoadCell_1.start(stabilizingTime, true);
  EEPROM.get(eeprom_a1, cv);
  LoadCell_1.setCalFactor(cv);
  while (!LoadCell_1.update());
  Serial.print("Started LC1 with calVal=");
  Serial.println(cv);

  Serial.println("Setup Done");
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
  digitalWrite(LED_PIN, LOW);
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
  waitForDebugButton(LED_PIN, 250); 
  LoadCell.update();
  LoadCell.refreshDataSet();

  // get and save new calFactor 
  float calVal = LoadCell.getNewCalibration(50.0);
  Serial.print("Got new calVal of ");
  Serial.println(LoadCell.getCalFactor());
  EEPROM.put(eeprom_loc, calVal);
  
}

void loop() {

  // pull data from the LCs, output to serial 
  if (LoadCell_1.update()){
    if ( millis() - lastPollTime > printInterval ){
      Serial.println(LoadCell_1.getData());
      lastPollTime = millis();}}

  // calibration command
  if (Serial.available() > 0){
    if (Serial.parseInt() == 1){
      calibrateLC(LoadCell_1, BLUE_LED, eeprom_a1);}}  
}