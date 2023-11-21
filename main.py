import tradingview_ta as tv_ta
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


INTERVAL, BBW, OPERATION, SCAN = range(4)

symbols_dir = 'exchanges/'
exchanges = ["BMFBOVESPA", "NASDAQ", "NYSE"]

input_exchange = "BMFBOVESPA"
input_interval = "5m"
input_bbw = "1.0"


def scan_symbols():
    """Scans for the Bollinger Bands width for multiple stocks at once"""
    available_symbols = open_file(input_exchange)

    analysis_dict = symbol_analysis(input_exchange, input_interval, available_symbols)

    return calculate_bbw_summary(analysis_dict, input_bbw)


def open_file(input_exchange):
    """Returns the stock ticker symbols available for the chosen exchange"""
    exchange_file = symbols_dir + input_exchange + ".txt"

    try:
        with open(exchange_file) as file:
            stock_symbols = file.read()
            file.close
    except:
        print("Something went wrong: Unable to read file!")
    else:
        return stock_symbols.split('\n')


def symbol_analysis(input_exchange, input_interval, available_symbols):
    """Returns a dictionary of a TradingView analysis of multiple stocks at once"""
    screener = "brazil" if input_exchange == "BMFBOVESPA" else "america"
    return tv_ta.get_multiple_analysis(screener=screener, interval=input_interval, symbols=available_symbols)


def calculate_bbw_summary(analysis_dict, input_bbw):
    """Returns the summary for multiple filtered symbols at once"""
    filtered_symbols = {}

    for symbol, value in analysis_dict.items():
        try:
            if symbol or value is not None:
                upper = value.indicators["BB.upper"]
                lower = value.indicators["BB.lower"]
                sma = value.indicators["SMA20"]

                bbw = (upper - lower) / sma

                if bbw < 1 and bbw < float(input_bbw):
                    bbw = round(bbw, 4)
                    filtered_symbols[symbol] = value.summary
        except TypeError:
            print(symbol, "is not defined!")
        except AttributeError:
            print(symbol, "is missing bbw calculation values!")
        except ZeroDivisionError:
            print(symbol, "bbw division by SMA zero value!")
    
    return filtered_symbols


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Selects the target exchange"""

    reply_keyboard = [exchanges]

    await update.message.reply_text(
        "Hi, I'm the Bollinger Bands Width Bot. I will hold a conversation with you.\nSend /cancel to stop talking to me!\n\n"
        "What is the target exchange?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Target exchange?"
        ),
    )

    return INTERVAL


async def interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Selects the target interval"""
    global input_exchange
    input_exchange = update.message.text
    
    await update.message.reply_text(
        "Please tell me your target interval - Options are:\n\n"
        "5m, 15m, 30m, 1h, 2h, 4h, 1d, 1W, 1M",
        reply_markup=ForceReply()
    )

    return BBW

async def bbw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Scans for the Bollinger Bands width""" 
    global input_interval
    input_interval = update.message.text
    
    await update.message.reply_text(
        "I see! Please tell me your target Bollinger Band width (less than 1.0)",
        reply_markup=ForceReply()
    )

    return OPERATION

async def operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Selects the target exchange"""
    try:
        if float(update.message.text) <= 1.0:
            global input_bbw
            input_bbw = update.message.text
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use a BBW value less than 1.0. Type /start to retry.")
            return ConversationHandler.END
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use a BBW value less than 1.0. Type /start to retry.")
        return ConversationHandler.END

    reply_keyboard = [["Strong\nBuy", "Buy", "Sell", "Strong\nSell"]]

    await update.message.reply_text(
        "What recommendations are you looking for?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Buying or Selling?"
        ),
    )

    return SCAN

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Scans and exibits for the requested recomendations"""
    filtered_symbols = scan_symbols()
    
    recommended_count = 0

    for symbol, value in filtered_symbols.items():
        stock = symbol.split(':', 1)
        
        recommendation = value["RECOMMENDATION"]
            
        if update.message.text == "Buy" and recommendation == "BUY":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock[1]}")
            recommended_count += 1    
        elif update.message.text == "Sell" and recommendation == "SELL":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock[1]}")
            recommended_count += 1    
        elif update.message.text == "Strong\nBuy" and recommendation == "STRONG_BUY":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock[1]}")
            recommended_count += 1    
        elif update.message.text == "Strong\nSell" and recommendation == "STRONG_SELL":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{stock[1]}")
            recommended_count += 1

    if recommended_count is not 0:
        await update.message.reply_text(f"There you go, here are your {recommended_count} {recommendation.replace('_', ' ')} recommendations! I hope we can /start a conversation again some day.")
    else:
        await update.message.reply_text("Sorry, there are no stocks to recommend at the moment using the given values.\nType /start to try again!")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Bye! I hope we can /start a conversation again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = (Application.builder()
                   .token("token here")
                   .build()
    )
    
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INTERVAL: [MessageHandler(filters.TEXT, interval)],
            BBW: [MessageHandler(filters.TEXT, bbw)],
            OPERATION: [MessageHandler(filters.TEXT, operation)],
            SCAN: [MessageHandler(filters.TEXT, scan)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()