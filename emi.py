from emiAi import EmiAI

API_KEY = "Emi-premium-22776249"

ai = EmiAI(API_KEY)

print("=" * 40)
print("🤖 EmiAI Terminal Bot")
print("برای خروج بنویس: exit")
print("=" * 40)

while True:
    try:
        message = input("\nYou: ")

        if message.lower() == "exit":
            print("🤖 خداحافظ 👋")
            break

        if not message.strip():
            continue

        print("🤖 EmiAI: در حال فکر کردن...")

        answer = ai.chat(message)

        print(f"🤖 EmiAI: {answer}")

    except KeyboardInterrupt:
        print("\n\n🤖 خداحافظ 👋")
        break

    except Exception as e:
        print(f"\n❌ خطا: {e}")
