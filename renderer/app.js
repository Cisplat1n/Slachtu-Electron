// -- Page Navigation --
function showPage(page) {
    document.getElementById('page-home').style.display = page === 'home' ? 'block' : 'none'
    document.getElementById('page-pipeline').style.display = page === 'pipeline' ? 'block' : 'none'
}


// -- Tab Navigation --
function showTab(index) {
    document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none')
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active'))

    document.getElementById(`tab-${index}`).style.display = 'block'
    document.querySelectorAll('.tab-btn')[index].classList.add('tab-active')

    // load review tab when opened
    if (index === 3) {
        loadReviewTab()
    }
}


// -- Load Review Tab -- 

function loadReviewTab() {
    const data = window.pipelineResult
    if (!data) return

    const container = document.getElementById('review-container')
    container.innerHTML = ''

    const functions = splitFunctions(data.cleaning_code)

    functions.forEach((fn, i) => {
        const nameMatch = fn.match(/def\s+(\w+)/)
        const name = nameMatch ? nameMatch[1] : `Function ${i+1}`

        const div = document.createElement('div')
        div.classList.add('function-block')

        div.innerHTML = `
            <label>
                <input type="checkbox" data-index="${i}" checked />
                ${name}
            </label>
            <pre>${fn}</pre>
        `

        container.appendChild(div)
    })
}


// -- Split code -- 

function splitFunctions(code) {
    return code
        .split(/(?=def\s+\w+\()/g)
        .map(f => f.trim())
        .filter(Boolean)
}

function getSelectedFunctions() {
    const checkboxes = document.querySelectorAll('#review-container input[type="checkbox"]')
    const functions = splitFunctions(window.pipelineResult.cleaning_code)

    return Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => functions[cb.dataset.index])
}

function getSelectedFunctions() {
    const checkboxes = document.querySelectorAll('#review-container input[type="checkbox"]')
    const functions = splitFunctions(window.pipelineResult.cleaning_code)

    return Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => functions[cb.dataset.index])
}


// -- Init --

document.addEventListener('DOMContentLoaded', () => {
    showTab(0)
    document.getElementById('csv-path').addEventListener('input', (e) => {
        const val = e.target.value
        document.getElementById('csv-status').textContent =
            val ? `Selected: ${val}` : 'No path entered'
    })
})


// -- Pipeline Call --

async function runPipeline() {
    const apiKey = document.getElementById('api-key').value
    const provider = document.getElementById('provider').value
    const csvPath = document.getElementById('csv-path').value
    const btn = document.getElementById('generate-btn')

    btn.disabled = true
    btn.textContent = 'Running...'
    document.getElementById('cleaning-code').textContent = ''

    try {
        const result = await window.api.runPipeline(csvPath, provider, apiKey)
        const json = JSON.parse(result)

        if (json.status === 'error') {
            document.getElementById('cleaning-code').textContent = `ERROR: ${json.message}`
        } else {
            // ONLY show status
            document.getElementById('cleaning-code').textContent = "Code generated successfully"

            // store globally
            window.pipelineResult = json
        }

    } catch (err) {
        document.getElementById('cleaning-code').textContent = `Error: ${err.message}`
    }

    btn.disabled = false
    btn.textContent = 'Generate Code'
}

