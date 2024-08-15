
import argparse
from client_module import DecentralizedClient

def main():
    parser = argparse.ArgumentParser(description="Decentralized Client CLI")
    parser.add_argument("--send", type=str, help="Отправить сообщение")
    parser.add_argument("--file", type=str, help="Отправить файл")
    
    args = parser.parse_args()
    
    client = DecentralizedClient(['192.168.178.10:8080'])
    client.connect()
    
    if args.send:
        client.send_message(args.send)
    if args.file:
        client.send_message(f"Отправка файла", args.file)

if __name__ == "__main__":
    main()
