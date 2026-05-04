```mermaid
flowchart TD
    A[Initialize]
    A --> B{Check Selenium}
        B -->|Selenium Driver Not Found| F
    B -->|Selenium Driver Found| C{Check CLI Tools}
        C -->|nmcli Not Found| F
        C -->|ping Not Found| F
    C -->|CLI Tools Working| D{Check Wifi Interface}
        D -->|Wifi Interface Not Found| F
        D -->|Wifi Interface Down| F
        D -->|Wifi Interface Up| E
    
    D --> E[Main Loop]
    E --> G

    F[Report Error and Exit]

    G{Check Internet Connection}
    G -->|Internet Up| H[Wait 5 Seconds]
    G -->|Internet Down| I[Scan Networks]
    H --> G
    I --> J[Check One Network]
    J --> K{Check For WPA Security}
    K -->|Secured| L{Check Known Networks}
        L -->|Network Known| L1[Attempt Connection Using nmcli]
        L -->|Network Not Known| J
        L1 --> L2{Check Internet Connection}
        L2 -->|Internet Down| J
        L2 -->|Internet Up| Z
    K -->|Open| M[Attempt Connection Using Selenium]
        M --> M1[Open non-DNS IP e.g. 1.1.1.1]
        M1 --> M2[Check All Boxes]
        M2 --> M3[Fill All Text Fields]
        M3 --> M4[Click Connection Button]
        M4 --> M5{Check Internet Connection}
        M5 -->|Internet Down| J
        M5 -->|Internet Up| Z

    Z[Wait 5 Seconds]
    Z --> G
```
