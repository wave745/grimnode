use anchor_lang::prelude::*;
use anchor_lang::system_program;

declare_id!("61f6dGaQnUjh7rD9Pp3FAJzpgwYExzqpi7fBwC6c17qm");

#[program]
pub mod grim_vault {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }

    pub fn subscribe(ctx: Context<Subscribe>, tier: u8) -> Result<()> {
        let subscription_account = &mut ctx.accounts.subscription_account;
        let user = &ctx.accounts.user;

        // Define subscription price (e.g., 0.1 SOL)
        let subscription_price: u64 = 100_000_000; // 0.1 SOL in lamports

        // Transfer SOL from user to program (treasury)
        // Transfer SOL from user to program (treasury)
        if ctx.accounts.grim_vault_program.key() != &ctx.program_id {
            return Err(ProgramError::InvalidAccountData.into());
        }
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: user.to_account_info(),
                    to: ctx.program_id.to_account_info(),
                },
            ),
            subscription_price,
        )?;

        subscription_account.subscriber = user.key();
        subscription_account.tier = tier;
        // Set subscription end date (e.g., 30 days from now)
        // For simplicity, using current timestamp + a fixed duration
        subscription_account.end_date = Clock::get()?.unix_timestamp + (30 * 24 * 60 * 60);

        msg!("Subscription created for user {:?} at tier {}", user.key(), tier);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}

#[derive(Accounts)]
pub struct Subscribe<'info> {
    #[account(init, payer = user, space = 8 + 32 + 1 + 8)] // Discriminator + Pubkey + u8 + i64
    pub subscription_account: Account<'info, SubscriptionAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct SubscriptionAccount {
    pub subscriber: Pubkey,
    pub tier: u8,
    pub end_date: i64,
}