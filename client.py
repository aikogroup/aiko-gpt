import asyncio
from langgraph_sdk import get_client
from langgraph_sdk.schema import Command
from langgraph_cli.exec import Runner


def get_langgraph_client():
    """Obtient le client LangGraph (mis en cache)"""
    return get_client(url="http://127.0.0.1:2024")


async def create_thread_and_dispatch(client, company_name, workshop_files, transcript_files):

    thread = await client.threads.create()
    print("Thread created:", thread["thread_id"])

    # Use wait() instead of create() + join()  
    state = await client.runs.wait(  
        thread_id=thread["thread_id"],  
        assistant_id="need_analysis",  
        input={  
            "company_info": {"company_name": company_name},  
            "workshop_files": workshop_files,  
            "transcript_files": transcript_files  
        },  
        # interrupt_before=["human_validation"]  
    )  
      
    return thread["thread_id"], state

async def human_validation(client, thread_id, validated_needs, rejected_needs, user_feedback):  
    # Get current state to access iteration_count  
    current_state = await client.threads.get_state(thread_id)  
    current_iteration = current_state['values'].get('iteration_count', 0)  
      
    # Clear current validated_needs to prevent accumulation  
    await client.threads.update_state(  
        thread_id,  
        values={  
            "validated_needs": [],  
            "rejected_needs": [],  
            "user_feedback": []  
        }  
    )  
      
    # Set new values AND add to history  
    await client.threads.update_state(  
        thread_id,  
        values={  
            "validated_needs": validated_needs,  
            "rejected_needs": rejected_needs,  
            "user_feedback": user_feedback,  
            # Add to history with correct iteration count  
            "validation_result": [{  
                "validated_needs": validated_needs,  
                "rejected_needs": rejected_needs,  
                "user_feedback": user_feedback,  
                "iteration": current_iteration  # Now properly defined  
            }]  
        }  
    )  
      
    # Resume execution  
    result = await client.runs.wait(thread_id, assistant_id="need_analysis", input=None)  
    return result

async def use_case_validation(  
    client,   
    thread_id,   
    validated_quick_wins,   
    validated_structuration_ia,  
    rejected_quick_wins,  
    rejected_structuration_ia,  
    user_feedback  
):  
    """  
    Handle use case validation by updating state and resuming the graph.  
      
    Args:  
        client: LangGraph SDK client  
        thread_id: Thread ID from create_thread_and_dispatch  
        validated_quick_wins: List of validated quick win use cases  
        validated_structuration_ia: List of validated structuration IA use cases  
        rejected_quick_wins: List of rejected quick win use cases  
        rejected_structuration_ia: List of rejected structuration IA use cases  
        user_feedback: User feedback string  
      
    Returns:  
        Final state after resuming execution  
    """  
    # Clear existing use case validation data to prevent accumulation  
    await client.threads.update_state(  
        thread_id,  
        values={  
            "validated_quick_wins": [],  
            "validated_structuration_ia": [],  
            "rejected_quick_wins": [],  
            "rejected_structuration_ia": []  
        }  
    )  
      
    # Set new validation values  
    await client.threads.update_state(  
        thread_id,  
        values={  
            "validated_quick_wins": validated_quick_wins,  
            "validated_structuration_ia": validated_structuration_ia,  
            "rejected_quick_wins": rejected_quick_wins,  
            "rejected_structuration_ia": rejected_structuration_ia,  
            "use_case_user_feedback": user_feedback,  
            # Add to history (if you have a history field with reducer)  
            "use_case_validation_result": [{  
                "validated_quick_wins": validated_quick_wins,  
                "validated_structuration_ia": validated_structuration_ia,  
                "rejected_quick_wins": rejected_quick_wins,  
                "rejected_structuration_ia": rejected_structuration_ia,  
                "user_feedback": user_feedback,  
                "iteration": state.get("use_case_iteration", 0)  
            }]  
        }  
    )  
      
    # Resume execution from the checkpoint  
    result = await client.runs.wait(  
        thread_id,  
        assistant_id="need_analysis",  
        input=None  
    )  
      
    return result


async def update_identified_need_theme(client, thread_id, need_id, new_theme):  
    """  
    Update the theme of a specific identified need.  
      
    Args:  
        client: LangGraph SDK client  
        thread_id: Thread ID  
        need_id: ID of the need to update (e.g., "need_1")  
        new_theme: New theme text  
    """  
    # Get current state  
    thread_state = await client.threads.get_state(thread_id)  
    current_needs = thread_state['values'].get('identified_needs', [])  
      
    # Find and update the specific need  
    updated_needs = []  
    for need in current_needs:  
        if need.get('id') == need_id:  
            # Update the theme  
            updated_need = need.copy()  
            updated_need['theme'] = new_theme  
            updated_needs.append(updated_need)  
        else:  
            updated_needs.append(need)  
      
    # Update state with modified needs  
    await client.threads.update_state(  
        thread_id,  
        values={"identified_needs": updated_needs}  
    )
        # Return the updated state so caller can verify the change  
    return await client.threads.get_state(thread_id)







if __name__ == "__main__":
    client = get_langgraph_client()

    # Exemple de données à adapter
    company_name = "peugeot"
    transcript_files = ["/Users/julliardcyril/Projets/aikoGPT/inputs/040425-Cousin-Biotech-x-aiko-R-D-090affe8-e55e.pdf"]
    workshop_files = ["/Users/julliardcyril/Projets/aikoGPT/inputs/atelier_exemple.xlsx"]
    validated_needs= [
    {
      "id": "need_1",
      "theme": "Automatisation de la gestion documentaire",
      "quotes": [
        "Gagner du temps dans la création de documents (flow charts, plaquettes marketing)",
        "Réduction des erreurs manuelles",
        "Automatiser la mise à jour des documents techniques lorsque des modifications sont apportées"
      ]
    },
    {
      "id": "need_2",
      "theme": "Amélioration de la productivité opérationnelle",
      "quotes": [
        "Gain de temps significatif sur le contrôle de conformité des produits",
        "Pour moi, c'est vraiment le point qui pourrait nous faire gagner énormément de temps.",
        "Ça nous fait gagner 50 % de performance en plus..."
      ]
    },
    {
      "id": "need_3",
      "theme": "Optimisation de la gestion des approvisionnements",
      "quotes": [
        "Commande automatique de composants",
        "Analyse des stocks pour anticiper les besoins",
        "Réduction du temps consacré à la gestion des commandes"
      ]
    },
    {
      "id": "need_4",
      "theme": "Sécurisation des données et systèmes",
      "quotes": [
        "Pas de cartographie existante des données et systèmes",
        "Absence d'outil de concentration des données",
        "On n'a pas d'outil qui vient récupérer tout ça et organiser tout ça."
      ]
    },
    {
      "id": "need_5",
      "theme": "Collaboration inter-départementale",
      "quotes": [
        "Collaborer efficacement avec différents départements pour la création des dossiers de conformité",
        "Besoin d'améliorer la collaboration entre les départements",
        "On veut cartographier ça."
      ]
    }
  ]
    rejected_needs= [
    {
      "id": "need_6",
      "theme": "Gestion avancée de la relation client",
      "quotes": [
        "Besoin non prioritaire pour le moment"
      ]
    }
  ]
    user_feedback= ["Les besoins 1 et 2 sont validés mais nous devons affiner les autres besoins identifiés. Le besoin 6 n'est pas prioritaire actuellement."]
    with Runner() as runner:  
        thread_id, state = runner.run(  
            create_thread_and_dispatch(client, company_name, workshop_files, transcript_files)  
        )  
        print(state['identified_needs'])
        print(f"Next nodes to execute: {state.get('next', [])}")
        print("########################################################")
        result = runner.run(  
            human_validation(client, thread_id, validated_needs, rejected_needs, user_feedback)  
        )  
        print("########################################################")
        print(result['validated_needs']) 
        print()
        print(result['identified_needs'])
        print()
        thread_state = runner.run(client.threads.get_state(thread_id))  
        print(f"Next nodes to execute 2: {thread_state.get('next', [])}")
        print("########################################################")