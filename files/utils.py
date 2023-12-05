# In order to avoid circular dependency errors you can put the function related to both files
# as it is in here that way you won't have any problems with that.

async def get_prefix(bot_instance, message):
    # Get default prefix from config file
    default_prefix = bot_instance.config['pref']['default_prefix']
    guild_id = str(message.guild.id)  # Convert the guild ID to string
    prefix = bot_instance.prefixes.get(guild_id, default_prefix)
    return prefix

