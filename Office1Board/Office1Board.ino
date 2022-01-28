
/*
 * Typical pin layout used:
 * ----------------------------------
 *             MFRC522      Node     
 *             Reader/PCD   MCU      
 * Signal      Pin          Pin      
 * ----------------------------------
 * RST/Reset   RST          D1 (GPIO5)        
 * SPI SS      SDA(SS)      D2 (GPIO4)       
 * SPI MOSI    MOSI         D7 (GPIO13)
 * SPI MISO    MISO         D6 (GPIO12)
 * SPI SCK     SCK          D5 (GPIO14)
 * 3.3V        3.3V         3.3V
 * GND         GND          GND
 */
#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

//******************************************************

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include <TZ.h>
#include <FS.h>
#include <LittleFS.h>
#include <CertStoreBearSSL.h>

// Update these with values suitable for your network.
const char *ssid = "where";
const char *password = "yaali110";
const char *mqtt_server = "9ac665715aee4617b293e90240ba8f5c.s2.eu.hivemq.cloud";

// A single, global CertStore which can be used by all connections.
// Needs to stay live the entire time any of the WiFiClientBearSSLs
// are present.
BearSSL::CertStore certStore;

WiFiClientSecure espClient;
PubSubClient *client;
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (500)
char msg[MSG_BUFFER_SIZE];
int value = 0;

//*******************************************************

const int trigPin = D0;
const int echoPin = D3;
const int led1_1 = D4;

float lightValue = 0;

char *user2 = "2803e714-51ce-4788-92c4-6eeaf4a1213e";
char *user1 = "f64982f3-a5c9-4c67-95ca-2ffc060f4c9a";

Servo servo;

constexpr uint8_t RST_PIN = 5; // Configurable, see typical pin layout above
constexpr uint8_t SS_PIN = 4;  // Configurable, see typical pin layout above
MFRC522 rfid(SS_PIN, RST_PIN); // Instance of the class
MFRC522::MIFARE_Key key;

// Init array that will store new NUID
byte nuidPICC[4];

// defines variables
long duration;
int distance;

void setup_wifi()
{
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void setDateTime()
{
  // You can use your own timezone, but the exact time is not used at all.
  // Only the date is needed for validating the certificates.
  configTime(TZ_Europe_Berlin, "pool.ntp.org", "time.nist.gov");

  Serial.print("Waiting for NTP time sync: ");
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2)
  {
    delay(100);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println();

  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  Serial.printf("%s %s", tzname[0], asctime(&timeinfo));
}

void callback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  char lightChar[10]; 
  for (int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
    lightChar[i] = (char)payload[i];
  }
  Serial.println();

  if (strcmp(topic,"smartoffice/light")==0)
  {
    lightValue = atof(lightChar);
    Serial.println(lightValue);
    analogWrite(led1_1, int(lightValue));
  }

  // Switch on the LED if the first character is present
  if ((char)payload[0] != NULL)
  {
//    digitalWrite(LED_BUILTIN, LOW); // Turn the LED on (Note that LOW is the voltage level
    // but actually the LED is on; this is because
    // it is active low on the ESP-01)
    delay(500);
//    digitalWrite(LED_BUILTIN, HIGH); // Turn the LED off by making the voltage HIGH
  }
  else
  {
//    digitalWrite(LED_BUILTIN, HIGH); // Turn the LED off by making the voltage HIGH
  }
}

void reconnect()
{
  delay(1000);
  // Loop until we’re reconnected
  while (!client->connected())
  {
    Serial.print("Attempting MQTT connection…");
    String clientId = "ESP8266Client - MyClient";
    // Attempt to connect
    // Insert your password
    if (client->connect(clientId.c_str(), "SAlireza78", "IoT@9731009"))
    {
      Serial.println("connected");
      // Once connected, publish an announcement…
      client->publish("smartoffice", "Smart office is running...");
      // … and resubscribe
      client->subscribe("smartoffice/#");
    }
    else
    {
      Serial.print("failed, rc = ");
      Serial.print(client->state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup()
{
  delay(1000);

  nuidPICC[3] = 0xA9;
  nuidPICC[2] = 0x33;
  nuidPICC[1] = 0x3D;
  nuidPICC[0] = 0xEC;
  
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(led1_1, OUTPUT);
  digitalWrite(led1_1, LOW);

  nuidPICC[3] = 0xA9;
  nuidPICC[2] = 0x33;
  nuidPICC[1] = 0x3D;
  nuidPICC[0] = 0xEC;

  servo.attach(D8);
  servo.write(0);
  Serial.begin(9600);

  SPI.begin();     // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522

  for (byte i = 0; i < 6; i++)
  {
    key.keyByte[i] = 0xFF;
  }

  Serial.println(F("This code scan the MIFARE Classsic NUID."));
  Serial.print(F("Using the following key:"));
  //  printHex(key.keyByte, MFRC522::MF_KEY_SIZE);
  Serial.println();
  servo.write(50);
  //**************************
  LittleFS.begin();
  setup_wifi();
  setDateTime();

  pinMode(LED_BUILTIN, OUTPUT); // Initialize the LED_BUILTIN pin as an output

  // you can use the insecure mode, when you want to avoid the certificates
  //espclient->setInsecure();

  int numCerts = certStore.initCertStore(LittleFS, PSTR("/certs.idx"), PSTR("/certs.ar"));
  Serial.printf("Number of CA certs read: %d\n", numCerts);
  if (numCerts == 0)
  {
    Serial.printf("No certs found. Did you run certs-from-mozilla.py and upload the LittleFS directory before running?\n");
    return; // Can't connect to anything w/o certs!
  }

  BearSSL::WiFiClientSecure *bear = new BearSSL::WiFiClientSecure();
  // Integrate the cert store with this connection
  bear->setCertStore(&certStore);

  client = new PubSubClient(*bear);

  client->setServer(mqtt_server, 8883);
  client->setCallback(callback);
}

void loop()
{
  if (!client->connected())
  {
    reconnect();
  }
  client->loop();
  if ( ! rfid.PICC_IsNewCardPresent())
    return;

  // Verify if the NUID has been readed
  if ( ! rfid.PICC_ReadCardSerial())
    return;

  
  Serial.println(F("The NUID tag is:"));
  printDec(rfid.uid.uidByte, rfid.uid.size);

  if (rfid.uid.uidByte[0] != nuidPICC[0] || 
    rfid.uid.uidByte[1] != nuidPICC[1] || 
    rfid.uid.uidByte[2] != nuidPICC[2] || 
    rfid.uid.uidByte[3] != nuidPICC[3] ) {
  
      client->publish("smartoffice/card", "1");
      client->publish("smartoffice/guid", user1);
      Serial.println("Publish message: 1");
      Serial.println("-----------------------------------------------");
  } else {
      client->publish("smartoffice/card", "2");
      client->publish("smartoffice/guid", user2);
      Serial.println("Publish message: 2");
      Serial.println("-----------------------------------------------");
    }

//  unsigned long now = millis();
//  if (now - lastMsg > 10000)
//  {
//    lastMsg = now;
//    ++value;
//    // snprintf(msg, MSG_BUFFER_SIZE, "hello world #%ld", value);
//    Serial.println("Publish message: 2");
//    // Serial.println(msg);
//    client->publish("smartoffice/card", card);
//  }

  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);

  // Calculating the distance
  distance = duration * 0.034 / 2;

  // Prints the distance on the Serial Monitor
  Serial.print("Distance: ");
  Serial.println(distance);
  delay(2000);

  // Halt PICC
  rfid.PICC_HaltA();

  // Stop encryption on PCD
  rfid.PCD_StopCrypto1();
}

float getFloat(byte packet[], int i)
{
  float out;
  memcpy(&out, &packet[i], sizeof(float));
  return out;
}

void printDec(byte *buffer, byte bufferSize)
{

  for (byte i = 0; i < bufferSize; i++)
  {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], DEC);
  }
  Serial.println();
}
