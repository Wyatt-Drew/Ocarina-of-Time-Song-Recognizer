/*Purpose: This is a MQTT client designed for a node mcu esp8266
 It controls the actuators responsible for causing song effects

 To use it update:
 1) Client_ID  - This is used to control arduino specific logic.  It also is used by the MQTT broker to identify the client.

 Code was adapted from Allen Pan's (Sufficiently Advanced) code
 https://github.com/Sufficiently-Advanced/ZeldaHomeAutomation/blob/master/zeldaReceiverPublic.ino
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>
// Network details
const char* ssid = "Access-E278";
const char* password = "rockyphoenix479";
const char* mqtt_server = "192.168.0.34";

WiFiClient espClient;
PubSubClient client(espClient);

//Client List
//1 = light, kettle, water pump
//2 = example servo
char client_ID = '1';

//GPIO pins
//Repeats are allowed for readability.  Repeats are used by different arduinos.
int lightPin = 4;     //D4 = GPIO2
int firePin = 2;      //D2 = GPIO4
int stormPin = 5;     //D1 = GPIO5
int examplePin = 5;
Servo fireServo;
Servo exampleServo;
int stormPause = 10000;

void setup() {
  pinMode(BUILTIN_LED, OUTPUT);// Initialize the BUILTIN_LED pin as an output
  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  //Client specific setup
  if (client_ID=='1') {
    //Servos - For servos write the angle then attach it to a pin
    fireServo.write(0);
    fireServo.attach(firePin); //fire
    //Pins - For pins attach it to output then initialize it
    pinMode(stormPin, OUTPUT); 
    pinMode(lightPin, OUTPUT);
    //Relay is lowTriggered so HIGH = off
    digitalWrite(stormPin, HIGH);
    digitalWrite(lightPin, HIGH);
  }
  if (client_ID=='2') {
    exampleServo.write(180); //Off state
    exampleServo.attach(examplePin);
  }
}
void setup_wifi() {//Purpose: Initial WiFi setup
  delay(10);
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected");
}
void reconnectMQTT() {//Purpose: Helper function to connect to MQTT broker
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(String(client_ID).c_str())) {//Unique name for each client
      Serial.println("connected");
      client.subscribe("songID");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}
void loop() {//Purpose: Loops forever, ensuring connection to MQTT broker
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
}
void callback(char* topic, byte* payload, unsigned int length) {//Purpose: When MQTT returns a message, this function gets called to handle it.
  Serial.println("song played");
  Serial.println();
  //Client specific actions
  if (client_ID=='1'){
    if ((char)payload[0]=='1') {digitalWrite(lightPin, LOW);}           //Sun song 'On' state
    if ((char)payload[0]=='2') {digitalWrite(lightPin, HIGH);}          //Song of Time 'Off' state
    if ((char)payload[0]=='3') {moveServoWithReset(fireServo, 150, 0);} //Boloro of Fire
    if ((char)payload[0]=='4') {pinHold(stormPause, stormPin);}         //Song of Storms
  }
  if (client_ID=='2'){
    if ((char)payload[0]=='1') {moveServo(exampleServo, 180, 0); }      //Sun song 'On' position
    if ((char)payload[0]=='2') {moveServo(exampleServo, 0, 180); }      //Song of Time 'Off' position
  }
}

//Helper functions
void moveServoWithReset(Servo thisServo, int onPosition, int offPosition) {//Purpose: Move servo to on position and back slowly
  moveServo(thisServo, offPosition, onPosition);
  moveServo(thisServo, onPosition, offPosition);
}
void moveServo(Servo myservo, int start, int end) {//Purpose: Slowly move servo from start to end position
  int pos;
  if (start < end){
    for(pos = start; pos <= end; pos += 1) {                                 
      myservo.write(pos);              
      delay(20);                      
    } 
  }else{
    for(pos = start; pos>=end; pos-=1){                                
      myservo.write(pos);            
      delay(20);                       
    } 
  }
}
void pinHold(int holdTime, int pin) {//Purpose: Hold pin low for holdtime, then switch back to high
  digitalWrite(pin, LOW);
  delay(holdTime);
  digitalWrite(pin, HIGH);
}