<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  function goBack() {
    dispatch('back');
  }

  let openQuestion = null;

  function toggleQuestion(index) {
    openQuestion = openQuestion === index ? null : index;
  }

  const questions = [
    {
      q: "What is AI Investment Scout DAO?",
      a: "AI Investment Scout DAO is a dashboard for evaluating and voting on startup investment opportunities. Proposals are created by the community, analyzed by an AI system, and then voted on using smart contracts for transparent governance."
    },
    {
      q: "How does the process work from start to finish?",
      a: `Create Proposal – A founder or scout submits an investment memo with key details.

AI Analysis – Our AI agent reviews the memo and market data, producing risk assessment and insights.

Smart Contract – The proposal and its metadata are recorded on-chain.

Vote & Execute – Community members vote. If the required threshold is met, the proposal is marked as approved and can be executed.`
    },
    {
      q: "What is the Dashboard showing me?",
      a: "The Dashboard lists all Investment Proposals as cards. Each card shows the project image, title, short description, current vote breakdown (Yes/No), and approval percentage. You can use the filters on the left to slice proposals by category (AI & ML, Healthcare, CleanTech, Web3, FinTech, etc.), status (Active, Approved, Rejected), and confidence distribution."
    },
    {
      q: "What can I do on the \"Create Proposal\" page?",
      a: "On the Create Proposal page you submit a new investment opportunity. You provide a Proposal Title, Executive Summary, IPFS CID for the full memo PDF, a Confidence Score (0–100), and optional metadata in JSON (for example: sector, funding stage, risk score)."
    },
    {
      q: "What is an IPFS CID and why do I need it?",
      a: "The IPFS CID is the unique content identifier of your full investment memo stored on IPFS (a decentralized storage network). We only store this CID on-chain and in the app, so anyone can verify that the proposal they see corresponds exactly to the document you uploaded."
    },
    {
      q: "What is the Confidence Score slider?",
      a: "The Confidence Score (0–100) represents how confident the AI (or the analyst) is in the proposal's risk-return profile. Higher scores indicate stronger conviction that the opportunity fits the DAO's criteria. This score is used for sorting and filtering proposals on the Dashboard."
    },
    {
      q: "What is the Metadata (Optional JSON) field for?",
      a: `The Metadata field lets you attach structured information to a proposal in JSON format, e.g.

{"sector": "tech", "stage": "series-a", "risk_score": 50}.

This makes it easy to filter, group, and analyze proposals by sector, stage, geography, or any other custom tags.`
    },
    {
      q: "How does voting on proposals work?",
      a: "Once a proposal is active, DAO members can cast a Yes or No vote. The vote progress bars on each card show the share of Yes vs No votes and the total vote count. When more than 50% of votes are Yes (or another configured threshold), the smart contract marks the proposal as approved."
    },
    {
      q: "What do the proposal statuses mean?",
      a: `Active – The proposal is open for voting.

Approved – The proposal reached the required Yes-vote threshold.

Rejected – The proposal failed to meet the threshold or was voted down.`
    },
    {
      q: "What role does the smart contract play?",
      a: "The Smart Contract ensures that proposals, votes, and final outcomes are tamper-proof and transparent. It enforces the voting rules (e.g. >50% Yes) and records when a proposal has been approved or rejected so the result can be trusted by everyone."
    },
    {
      q: "How is AI used in the platform?",
      a: "The AI system analyzes submitted proposals to provide risk assessment, market insights, and a confidence score. The goal is not to replace human judgment but to give voters a structured, data-driven view that makes it easier to compare opportunities."
    },
    {
      q: "Who is this platform for?",
      a: "The platform is designed for founders, investment scouts, and DAO communities who want a streamlined, transparent way to submit, analyze, and vote on investment opportunities—combining AI analysis with on-chain governance."
    }
  ];
</script>

<div class="space-y-6 animate-fade-in">
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="font-display text-4xl font-bold text-pe-text">Q&A</h1>
      <p class="text-pe-muted mt-2">Frequently asked questions</p>
    </div>
    
    <button class="flex items-center gap-2 px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors focus-ring" on:click={goBack}>
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      Back
    </button>
  </div>
  
  <!-- Questions -->
  <div class="space-y-4">
    {#each questions as question, index}
      <div class="card-pe overflow-hidden">
        <button
          class="w-full flex items-center justify-between p-6 text-left hover:bg-pe-panel/50 transition-colors focus-ring"
          on:click={() => toggleQuestion(index)}
        >
          <span class="font-display font-semibold text-lg text-pe-text pr-4">
            Q{index + 1}. {question.q}
          </span>
          <svg
            class="h-5 w-5 text-pe-muted flex-shrink-0 transition-transform {openQuestion === index ? 'rotate-180' : ''}"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {#if openQuestion === index}
          <div class="px-6 pb-6 pt-0">
            <div class="text-pe-muted leading-relaxed whitespace-pre-line">
              {question.a}
            </div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
</style>
